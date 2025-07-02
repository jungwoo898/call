#!/usr/bin/env python3
"""
Callytics 상담사 인증 시스템
로그인, 권한 관리, 세션 관리
"""

import hashlib
import secrets
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import jwt
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AgentSession:
    """상담사 세션 정보"""
    agent_id: int
    username: str
    full_name: str
    department: str
    position: str
    permissions: List[str]
    session_token: str
    expires_at: datetime

class AgentAuthManager:
    """상담사 인증 관리자"""
    
    def __init__(self, db_path: str = "data/callytics_consultation_quality.db"):
        self.db_path = db_path
        self.secret_key = "your-secret-key-here"  # 실제 운영시 환경변수로 관리
        self.session_duration = timedelta(hours=8)  # 세션 유지 시간
    
    @contextmanager
    def get_db_connection(self):
        """데이터베이스 연결"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def hash_password(self, password: str) -> str:
        """비밀번호 해시화"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return f"{salt}${hash_obj.hex()}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        try:
            salt, hash_hex = hashed_password.split('$')
            hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return hash_obj.hex() == hash_hex
        except:
            return False
    
    def create_agent_account(self, username: str, email: str, password: str, 
                           full_name: str, department: str, position: str, 
                           employee_id: str = None) -> Optional[int]:
        """상담사 계정 생성"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 계정 생성
                hashed_password = self.hash_password(password)
                cursor.execute("""
                    INSERT INTO agent_accounts (username, email, password_hash)
                    VALUES (?, ?, ?)
                """, (username, email, hashed_password))
                
                account_id = cursor.lastrowid
                
                # 프로필 생성
                cursor.execute("""
                    INSERT INTO agent_profiles (account_id, employee_id, full_name, first_name, last_name, department, position)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (account_id, employee_id, full_name, full_name.split()[0], ' '.join(full_name.split()[1:]), department, position))
                
                agent_id = cursor.lastrowid
                
                # 기본 권한 부여
                cursor.execute("""
                    INSERT INTO agent_permissions (agent_id, permission_type, permission_level)
                    VALUES (?, 'audio_upload', 'write')
                """, (agent_id,))
                
                cursor.execute("""
                    INSERT INTO agent_permissions (agent_id, permission_type, permission_level)
                    VALUES (?, 'analysis_view', 'read')
                """, (agent_id,))
                
                # 기본 설정 생성
                cursor.execute("""
                    INSERT INTO agent_settings (agent_id)
                    VALUES (?)
                """, (agent_id,))
                
                conn.commit()
                logger.info(f"상담사 계정 생성 완료: {username} ({full_name})")
                return agent_id
                
        except sqlite3.IntegrityError as e:
            logger.error(f"계정 생성 실패 (중복): {e}")
            return None
        except Exception as e:
            logger.error(f"계정 생성 실패: {e}")
            return None
    
    def authenticate_agent(self, username: str, password: str) -> Optional[AgentSession]:
        """상담사 인증"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 계정 정보 조회
                cursor.execute("""
                    SELECT aa.*, ap.*
                    FROM agent_accounts aa
                    JOIN agent_profiles ap ON aa.id = ap.account_id
                    WHERE aa.username = ? AND aa.account_status = 'active'
                """, (username,))
                
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"인증 실패: 사용자를 찾을 수 없음 - {username}")
                    return None
                
                # 계정 잠금 확인
                if row['account_locked_until'] and datetime.fromisoformat(row['account_locked_until']) > datetime.now():
                    logger.warning(f"인증 실패: 계정 잠금 - {username}")
                    return None
                
                # 비밀번호 검증
                if not self.verify_password(password, row['password_hash']):
                    # 로그인 실패 횟수 증가
                    cursor.execute("""
                        UPDATE agent_accounts 
                        SET login_attempts = login_attempts + 1
                        WHERE id = ?
                    """, (row['id']))
                    
                    # 5회 실패시 계정 잠금
                    if row['login_attempts'] >= 4:
                        lock_until = datetime.now() + timedelta(minutes=30)
                        cursor.execute("""
                            UPDATE agent_accounts 
                            SET account_locked_until = ?
                            WHERE id = ?
                        """, (lock_until.isoformat(), row['id']))
                        logger.warning(f"계정 잠금: {username} (5회 실패)")
                    
                    conn.commit()
                    logger.warning(f"인증 실패: 잘못된 비밀번호 - {username}")
                    return None
                
                # 로그인 성공 - 실패 횟수 초기화
                cursor.execute("""
                    UPDATE agent_accounts 
                    SET login_attempts = 0, account_locked_until = NULL, last_login_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (row['id']))
                
                # 권한 조회
                cursor.execute("""
                    SELECT permission_type, permission_level
                    FROM agent_permissions
                    WHERE agent_id = ? AND is_active = 1
                """, (row['agent_id'],))
                
                permissions = [f"{row['permission_type']}:{row['permission_level']}" for row in cursor.fetchall()]
                
                # 세션 토큰 생성
                session_token = secrets.token_urlsafe(32)
                expires_at = datetime.now() + self.session_duration
                
                # 활동 로그 기록
                cursor.execute("""
                    INSERT INTO agent_activity_logs (agent_id, activity_type, activity_description)
                    VALUES (?, 'login', '로그인 성공')
                """, (row['agent_id'],))
                
                conn.commit()
                
                session = AgentSession(
                    agent_id=row['agent_id'],
                    username=row['username'],
                    full_name=row['full_name'],
                    department=row['department'],
                    position=row['position'],
                    permissions=permissions,
                    session_token=session_token,
                    expires_at=expires_at
                )
                
                logger.info(f"인증 성공: {username} ({row['full_name']})")
                return session
                
        except Exception as e:
            logger.error(f"인증 처리 실패: {e}")
            return None
    
    def validate_session(self, session_token: str) -> Optional[AgentSession]:
        """세션 검증"""
        # 실제 구현에서는 Redis나 DB에 세션 정보 저장
        # 여기서는 간단한 예시로 JWT 토큰 사용
        try:
            payload = jwt.decode(session_token, self.secret_key, algorithms=['HS256'])
            
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ap.*, aa.username
                    FROM agent_profiles ap
                    JOIN agent_accounts aa ON ap.account_id = aa.id
                    WHERE ap.id = ? AND ap.is_active = 1 AND aa.account_status = 'active'
                """, (payload['agent_id'],))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # 권한 조회
                cursor.execute("""
                    SELECT permission_type, permission_level
                    FROM agent_permissions
                    WHERE agent_id = ? AND is_active = 1
                """, (payload['agent_id'],))
                
                permissions = [f"{row['permission_type']}:{row['permission_level']}" for row in cursor.fetchall()]
                
                return AgentSession(
                    agent_id=row['id'],
                    username=row['username'],
                    full_name=row['full_name'],
                    department=row['department'],
                    position=row['position'],
                    permissions=permissions,
                    session_token=session_token,
                    expires_at=datetime.fromisoformat(payload['expires_at'])
                )
                
        except jwt.ExpiredSignatureError:
            logger.warning("세션 만료")
            return None
        except jwt.InvalidTokenError:
            logger.warning("잘못된 세션 토큰")
            return None
        except Exception as e:
            logger.error(f"세션 검증 실패: {e}")
            return None
    
    def create_session_token(self, agent_session: AgentSession) -> str:
        """세션 토큰 생성"""
        payload = {
            'agent_id': agent_session.agent_id,
            'username': agent_session.username,
            'expires_at': agent_session.expires_at.isoformat(),
            'exp': agent_session.expires_at.timestamp()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def logout_agent(self, agent_id: int, session_token: str):
        """로그아웃"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 활동 로그 기록
                cursor.execute("""
                    INSERT INTO agent_activity_logs (agent_id, activity_type, activity_description)
                    VALUES (?, 'logout', '로그아웃')
                """, (agent_id,))
                
                conn.commit()
                logger.info(f"로그아웃 완료: agent_id={agent_id}")
                
        except Exception as e:
            logger.error(f"로그아웃 처리 실패: {e}")
    
    def get_agent_permissions(self, agent_id: int) -> List[str]:
        """상담사 권한 조회"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT permission_type, permission_level
                    FROM agent_permissions
                    WHERE agent_id = ? AND is_active = 1
                """, (agent_id,))
                
                return [f"{row['permission_type']}:{row['permission_level']}" for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"권한 조회 실패: {e}")
            return []
    
    def check_permission(self, agent_id: int, permission_type: str, required_level: str = 'read') -> bool:
        """권한 확인"""
        permissions = self.get_agent_permissions(agent_id)
        
        for permission in permissions:
            perm_type, perm_level = permission.split(':')
            if perm_type == permission_type:
                if required_level == 'read' and perm_level in ['read', 'write', 'admin']:
                    return True
                elif required_level == 'write' and perm_level in ['write', 'admin']:
                    return True
                elif required_level == 'admin' and perm_level == 'admin':
                    return True
        
        return False
    
    def log_activity(self, agent_id: int, activity_type: str, description: str = None, 
                    ip_address: str = None, user_agent: str = None, activity_data: str = None):
        """활동 로그 기록"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO agent_activity_logs 
                    (agent_id, activity_type, activity_description, ip_address, user_agent, activity_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (agent_id, activity_type, description, ip_address, user_agent, activity_data))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"활동 로그 기록 실패: {e}")
    
    def get_agent_profile(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """상담사 프로필 조회"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ap.*, aa.username, aa.email, aa.last_login_at
                    FROM agent_profiles ap
                    JOIN agent_accounts aa ON ap.account_id = aa.id
                    WHERE ap.id = ?
                """, (agent_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"프로필 조회 실패: {e}")
            return None
    
    def update_agent_profile(self, agent_id: int, **kwargs) -> bool:
        """상담사 프로필 업데이트"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 업데이트 가능한 필드들
                allowed_fields = ['full_name', 'first_name', 'last_name', 'department', 'position', 
                                'team', 'specialization', 'contact_number', 'bio']
                
                update_fields = []
                update_values = []
                
                for field, value in kwargs.items():
                    if field in allowed_fields and value is not None:
                        update_fields.append(f"{field} = ?")
                        update_values.append(value)
                
                if not update_fields:
                    return False
                
                update_values.append(agent_id)
                
                cursor.execute(f"""
                    UPDATE agent_profiles 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, update_values)
                
                conn.commit()
                logger.info(f"프로필 업데이트 완료: agent_id={agent_id}")
                return True
                
        except Exception as e:
            logger.error(f"프로필 업데이트 실패: {e}")
            return False 