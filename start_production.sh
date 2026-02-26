#!/bin/bash

# 프로덕션 환경 실행 스크립트

echo "🚀 프로덕션 환경 시작..."

# 가상 환경 활성화
source venv/bin/activate

# 환경변수 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사하세요"
    cp .env.example .env
    echo "✅ .env 파일 생성 완료"
    echo "⚠️  SECRET_KEY를 반드시 변경하세요!"
    exit 1
fi

# 로그 디렉토리 생성
mkdir -p logs

# 데이터베이스 마이그레이션
echo "📊 데이터베이스 마이그레이션..."
python init_db.py

# 서비스 시작
echo "🌐 FastAPI 서버 시작 (포트 8001)..."
uvicorn fastapi_app.main:app --host 0.0.0.0 --port 8001 --workers 4 &
FASTAPI_PID=$!

echo "⏳ Celery Worker 시작..."
celery -A fastapi_app.tasks.celery_app worker --loglevel=info --concurrency=4 &
CELERY_PID=$!

echo "🌸 Flower 모니터링 시작 (포트 5555)..."
celery -A fastapi_app.tasks.celery_app flower --port=5555 --basic_auth=admin:password123 &
FLOWER_PID=$!

echo ""
echo "✅ 모든 서비스가 시작되었습니다!"
echo ""
echo "📍 접속 주소:"
echo "  - API: http://localhost:8001"
echo "  - API 문서: http://localhost:8001/docs"
echo "  - Flower 모니터링: http://localhost:5555 (admin/password123)"
echo ""
echo "프로세스 ID:"
echo "  - FastAPI: $FASTAPI_PID"
echo "  - Celery: $CELERY_PID"
echo "  - Flower: $FLOWER_PID"
echo ""
echo "종료하려면 Ctrl+C 또는 ./stop.sh"
echo ""

# PID 저장
echo $FASTAPI_PID > fastapi.pid
echo $CELERY_PID > celery.pid
echo $FLOWER_PID > flower.pid

# 대기
wait
