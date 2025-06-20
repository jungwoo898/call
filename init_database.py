#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
"""

import sqlite3
import os
from pathlib import Path

def init_database():
    """데이터베이스 초기화"""
    # 데이터베이스 파일 경로
    db_path = "Callytics_new.sqlite"
    
    # 기존 데이터베이스 파일이 있으면 삭제 (권한 문제 해결)
    if os.path.exists(db_path):
        print(f"기존 데이터베이스 파일 삭제: {db_path}")
        try:
            os.remove(db_path)
        except PermissionError:
            print(f"권한 오류로 삭제 실패, 새 파일명으로 생성")
            db_path = "Callytics_docker.sqlite"
    
    # 데이터베이스 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # EnhancedSchema.sql 파일 읽기
        schema_path = Path("src/db/sql/EnhancedSchema.sql")
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # SQL 문장들을 분리하여 실행
            cursor.executescript(schema_sql)
            conn.commit()
            print("✅ 데이터베이스 스키마가 성공적으로 생성되었습니다.")
            
            # 테이블 목록 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"📋 생성된 테이블: {[table[0] for table in tables]}")
        else:
            print(f"❌ 스키마 파일을 찾을 수 없습니다: {schema_path}")
            return False
        
        # --- 뷰 생성 구문 별도 실행 ---
        views_path = Path("src/db/sql/CreateViews.sql")
        if views_path.exists():
            with open(views_path, 'r', encoding='utf-8') as f:
                views_sql = f.read()
            cursor.executescript(views_sql)
            conn.commit()
            print("✅ 통계 뷰가 성공적으로 생성되었습니다.")
        else:
            print(f"⚠️ 뷰 생성 파일이 없습니다: {views_path}")
        
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 중 오류 발생: {e}")
        return False
    
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    print("🚀 Callytics 데이터베이스 초기화 시작...")
    
    if init_database():
        print("🎉 데이터베이스 초기화가 완료되었습니다!")
    else:
        print("❌ 데이터베이스 초기화에 실패했습니다.") 