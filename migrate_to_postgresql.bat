@echo off
REM ========================================================================
REM 🚀 Callytics SQLite → PostgreSQL 완전 마이그레이션 실행 스크립트
REM ========================================================================

echo ============================================================
echo 🚀 Callytics PostgreSQL 마이그레이션 시작
echo ============================================================

REM 환경변수 설정
if not exist .env (
    echo ⚠️ .env 파일을 복사하여 환경변수를 설정하세요
    copy env.template .env
    echo ✅ env.template을 .env로 복사했습니다
    echo 📝 .env 파일을 편집하여 PostgreSQL 설정을 확인하세요
    pause
)

REM 환경변수 로드
call .env 2>nul

REM 기본값 설정
if "%POSTGRES_HOST%"=="" set POSTGRES_HOST=localhost
if "%POSTGRES_PORT%"=="" set POSTGRES_PORT=5432
if "%POSTGRES_DB%"=="" set POSTGRES_DB=callytics
if "%POSTGRES_USER%"=="" set POSTGRES_USER=callytics_user
if "%POSTGRES_PASSWORD%"=="" set POSTGRES_PASSWORD=secure_password

echo 📋 마이그레이션 설정:
echo   - SQLite: Callytics_new.sqlite
echo   - PostgreSQL: %POSTGRES_HOST%:%POSTGRES_PORT%/%POSTGRES_DB%
echo   - 사용자: %POSTGRES_USER%
echo.

REM SQLite 파일 존재 확인
if not exist "Callytics_new.sqlite" (
    echo ❌ SQLite 파일이 없습니다: Callytics_new.sqlite
    echo 📁 현재 디렉토리에 SQLite 파일이 있는지 확인하세요
    pause
    exit /b 1
)

REM PostgreSQL 스키마 파일 확인
if not exist "src\db\sql\postgresql_migration_schema.sql" (
    echo ❌ PostgreSQL 스키마 파일이 없습니다
    echo 📁 src/db/sql/postgresql_migration_schema.sql 파일을 확인하세요
    pause
    exit /b 1
)

echo 🔍 1단계: PostgreSQL 연결 테스트
REM PostgreSQL 연결 테스트
python -c "
import asyncio
import asyncpg
import os

async def test_connection():
    try:
        conn = await asyncpg.connect(
            host='%POSTGRES_HOST%',
            port=%POSTGRES_PORT%,
            database='%POSTGRES_DB%',
            user='%POSTGRES_USER%',
            password='%POSTGRES_PASSWORD%'
        )
        await conn.close()
        print('✅ PostgreSQL 연결 성공')
        return True
    except Exception as e:
        print(f'❌ PostgreSQL 연결 실패: {e}')
        return False

if asyncio.run(test_connection()):
    exit(0)
else:
    exit(1)
"

if %errorlevel% neq 0 (
    echo.
    echo ❌ PostgreSQL 연결에 실패했습니다
    echo 🔧 해결 방법:
    echo   1. PostgreSQL 서버가 실행 중인지 확인
    echo   2. .env 파일의 연결 정보가 올바른지 확인
    echo   3. 방화벽 설정 확인
    echo   4. PostgreSQL 사용자 권한 확인
    echo.
    pause
    exit /b 1
)

echo.
echo 🐳 2단계: Docker 컨테이너 중지 (충돌 방지)
docker-compose -f docker-compose-microservices.yml down

echo.
echo 🐳 3단계: PostgreSQL 컨테이너 시작
docker-compose -f docker-compose-microservices.yml up -d postgres

echo.
echo ⏳ PostgreSQL 준비 대기 중...
timeout /t 15 /nobreak > nul

echo.
echo 🗄️ 4단계: PostgreSQL 스키마 생성
REM 스키마 생성 (Docker 컨테이너 내에서 실행)
docker exec -i callytics-postgres psql -U %POSTGRES_USER% -d %POSTGRES_DB% < src\db\sql\postgresql_migration_schema.sql

if %errorlevel% neq 0 (
    echo ❌ PostgreSQL 스키마 생성 실패
    echo 💡 수동으로 스키마를 생성해보세요:
    echo    docker exec -it callytics-postgres psql -U %POSTGRES_USER% -d %POSTGRES_DB%
    pause
    exit /b 1
)

echo ✅ PostgreSQL 스키마 생성 완료

echo.
echo 📋 5단계: 데이터 마이그레이션 실행
REM Python 마이그레이션 스크립트 실행
python src\db\migrate_to_postgresql.py

if %errorlevel% neq 0 (
    echo ❌ 데이터 마이그레이션 실패
    echo 📝 migration.log 파일을 확인하세요
    pause
    exit /b 1
)

echo.
echo 🔍 6단계: 데이터 무결성 검증
python -c "
import asyncio
import asyncpg
import os

async def verify_data():
    try:
        conn = await asyncpg.connect(
            host='%POSTGRES_HOST%',
            port=%POSTGRES_PORT%,
            database='%POSTGRES_DB%',
            user='%POSTGRES_USER%',
            password='%POSTGRES_PASSWORD%'
        )
        
        # 주요 테이블 레코드 수 확인
        tables = [
            'audio_files',
            'consultation_sessions', 
            'consultation_analysis',
            'transcriptions',
            'sentiment_analysis'
        ]
        
        print('📊 데이터 검증 결과:')
        total_records = 0
        
        for table in tables:
            try:
                count = await conn.fetchval(f'SELECT COUNT(*) FROM {table}')
                total_records += count
                print(f'  ✅ {table}: {count:,}개 레코드')
            except Exception as e:
                print(f'  ⚠️ {table}: 확인 실패 - {e}')
        
        print(f'\\n🔢 총 레코드 수: {total_records:,}개')
        
        await conn.close()
        return total_records > 0
        
    except Exception as e:
        print(f'❌ 데이터 검증 실패: {e}')
        return False

if asyncio.run(verify_data()):
    exit(0)
else:
    exit(1)
"

if %errorlevel% neq 0 (
    echo ❌ 데이터 검증 실패
    pause
    exit /b 1
)

echo.
echo 🔄 7단계: SQLite 백업 생성
if exist "Callytics_new.sqlite" (
    set backup_name=Callytics_backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sqlite
    set backup_name=%backup_name: =0%
    copy "Callytics_new.sqlite" "%backup_name%"
    echo ✅ SQLite 백업 생성: %backup_name%
)

echo.
echo ============================================================
echo 🎉 마이그레이션 완료!
echo ============================================================
echo.
echo ✅ SQLite → PostgreSQL 마이그레이션이 성공적으로 완료되었습니다
echo.
echo 📋 다음 단계:
echo   1. 모든 마이크로서비스 재시작
echo   2. API 엔드포인트 테스트
echo   3. 데이터 정합성 최종 확인
echo.
echo 🚀 마이크로서비스 재시작하려면 다음 명령을 실행하세요:
echo   docker-compose -f docker-compose-microservices.yml up -d
echo.
echo 📝 마이그레이션 로그: migration.log
echo 📋 백업 파일: %backup_name%
echo.

pause
exit /b 0 