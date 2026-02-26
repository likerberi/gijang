#!/bin/bash

# 개발 환경 통합 실행 스크립트
# 모든 서비스를 한 번에 시작합니다

set -e

echo "🚀 개발 환경 시작..."
echo ""

# 가상 환경 활성화
source venv/bin/activate

# 로그 디렉토리 생성
mkdir -p logs

# 기존 프로세스 정리
echo "🧹 기존 프로세스 정리 중..."
pkill -f "uvicorn fastapi_app" 2>/dev/null || true
pkill -f "celery.*fastapi_app" 2>/dev/null || true
pkill -f "celery.*config" 2>/dev/null || true
pkill -f "python manage.py runserver" 2>/dev/null || true
sleep 1

# Redis 확인
if ! redis-cli ping > /dev/null 2>&1; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  Redis가 실행 중이지 않습니다."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📌 명령어: redis-server --daemonize yes"
    echo "📋 기능: 인메모리 데이터베이스 (Key-Value Store)"
    echo "🔧 역할: Celery 메시지 브로커 (작업 큐 관리)"
    echo "   - Celery가 작업을 전달받고 결과를 저장하는 중간 매개체"
    echo "   - 고속 캐싱 및 임시 데이터 저장"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 데이터베이스 초기화..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📌 명령어: python init_db.py"
    echo "📋 기능: SQLAlchemy 테이블 생성"
    echo "🔧 역할: 데이터베이스 스키마 초기화"
    echo "   - users, documents, extracted_data, reports 테이블 생성"
    echo "   - 개발 환경에서는 SQLite3 사용"
    echo ""
    python init_db.py
    echo ""emonize yes
    sleep 2
fi
echo "✅ Redis 실행 중 (127.0.0.1:6379)"
echo ""

# 데이터베이스 초기화 (처음 실행 시)
if [ ! -f "fastapi_db.sqlite3" ]; then
    echo "📊 데이터베이스 초기화..."
    python init_db.py
fi

# FastAPI 서버 시작
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 FastAPI 서버 시작 (포트 8001)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📌 명령어: python -m uvicorn fastapi_app.main:app --reload --port 8001"
echo "📋 기능: Python ASGI 웹 서버 (비동기 고성능)"
echo "🔧 역할: REST API 요청 처리, HTTP 엔드포인트 서빙"
echo "   - --reload: 코드 변경 시 자동 재시작 (개발 모드)"
echo "   - --port 8001: 8001번 포트 사용"
echo ""
nohup python -m uvicorn fastapi_app.main:app --reload --port 8001 > logs/fastapi.log 2>&1 &
FASTAPI_PID=$!
echo $FASTAPI_PID > .fastapi.pid
sleep 2

# Celery Worker 시작
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⏳ Celery Worker 시작..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📌 명령어: celery -A fastapi_app.tasks.celery_app worker --loglevel=info"
echo "📋 기능: 분산 비동기 태스크 큐 워커"
echo "🔧 역할: 백그라운드 작업 처리 (파일 처리, 리포트 생성)"
echo "   - worker: 작업자 프로세스 실행"
echo "   - --loglevel=info: 정보 수준 로그 출력"
echo "   ⚡ Redis를 통해 태스크를 받아 비동기로 처리"
echo ""
nohup celery -A fastapi_app.tasks.celery_app worker --loglevel=info -n fastapi_worker@%h > logs/celery.log 2>&1 &
CELERY_PID=$!
echo $CELERY_PID > .celery.pid
sleep 2

# Django Celery Worker 시작
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⏳ Django Celery Worker 시작..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📌 명령어: celery -A config worker --loglevel=info"
echo "📋 기능: Django 측 문서 처리 / 파일 병합 태스크 처리"
echo ""
nohup celery -A config worker --loglevel=info -n django_worker@%h > logs/celery_django.log 2>&1 &
DJANGO_CELERY_PID=$!
echo $DJANGO_CELERY_PID > .celery_django.pid
sleep 2

# Django 서버 시작
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Django 서버 시작 (포트 8000)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📌 명령어: python manage.py runserver 0.0.0.0:8000"
echo "📋 기능: Django 웹 UI + REST API (회원가입, 문서관리, 사용가이드)"
echo ""
nohup python manage.py runserver 0.0.0.0:8000 > logs/django.log 2>&1 &
DJANGO_PID=$!
echo $DJANGO_PID > .django.pid
sleep 2

# Flow━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 모든 서비스가 시작되었습니다!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 접속 주소:"
echo "  🌐 Django UI:     http://localhost:8000/app/  (웹 프론트엔드)"
echo "  ❓ 사용 가이드:   http://localhost:8000/guide/"
echo "  🌐 FastAPI:      http://localhost:8001"
echo "  📚 API 문서:    http://localhost:8001/docs  (Swagger UI)"
if [ "$1" == "--with-flower" ] || [ "$1" == "-f" ]; then
    echo "  🌸 Flower:      http://localhost:5555 (admin/password123)"
fi
echo ""
echo "📊 로그 확인:"
echo "  tail -f logs/fastapi.log  # FastAPI 서버 로그"
echo "  tail -f logs/celery.log   # Celery Worker 로그"
if [ "$1" == "--with-flower" ] || [ "$1" == "-f" ]; then
    echo "  tail -f logs/flower.log   # Flower 로그"
fi
echo "  ./logs_dev.sh             # 통합 컬러 로그 (추천)"
echo ""
echo "💡 팁:"
echo "  - FastAPI는 코드 변경 시 자동으로 재시작됩니다 (--reload 모드)"
echo "  - Celery나 설정 변경 시: ./restart_dev.sh"
echo "  - 작업 모니터링: http://localhost:5555 (Flower 실행 시)"
echo "🔍 서비스 상태 확인..."
echo ""
if ps -p $FASTAPI_PID > /dev/null; then
    echo "✅ FastAPI 서버 정상 실행 중 (PID: $FASTAPI_PID)"
    echo "   → Uvicorn ASGI 서버가 HTTP 요청 대기 중"
else
    echo "❌ FastAPI 서버 시작 실패!"
    echo "   → logs/fastapi.log 확인: tail -f logs/fastapi.log"
fi

if ps -p $CELERY_PID > /dev/null; then
    echo "✅ Celery Worker 정상 실행 중 (PID: $CELERY_PID)"
    echo "   → 백그라운드 작업 처리 준비 완료"
else
    echo "❌ Celery Worker 시작 실패!"
    echo "   → logs/celery.log 확인: tail -f logs/celery.log"
fi

if [ "$1" == "--with-flower" ] || [ "$1" == "-f" ]; then
    if ps -p $FLOWER_PID > /dev/null; then
        echo "✅ Flower 정상 실행 중 (PID: $FLOWER_PID)"
        echo "   → Celery 모니터링 대시보드 준비 완료"
    else
        echo "❌ Flower 시작 실패!"
        echo "   → logs/flower.log 확인: tail -f logs/flower.log"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 각 서비스의 역할:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔄 요청 처리 흐름:"
echo "   1️⃣  사용자 → FastAPI (HTTP 요청)"
echo "   2️⃣  FastAPI → Redis (Celery 태스크 등록)"
echo "   3️⃣  Celery Worker → Redis (태스크 가져옴)"
echo "   4️⃣  Celery Worker (파일 처리 실행)"
echo "   5️⃣  Celery Worker → Database (결과 저장)"
echo "   6️⃣  사용자 → FastAPI (결과 조회)"
echo ""
echo "🧩 각 컴포넌트:"
echo "   🌐 FastAPI:  실시간 HTTP 요청/응답 처리"
echo "   ⏱️  Celery:   느린 작업을 백그라운드에서 처리"
echo "   📦 Redis:    Celery 작업 큐 및 결과 저장"
echo "   💾 SQLite:   사용자/문서 메타데이터 영구 저장"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 상태 체크
sleep 2
if ps -p $FASTAPI_PID > /dev/null; then
    echo "✅ FastAPI 서버 정상 실행 중 (PID: $FASTAPI_PID)"
else
    echo "❌ FastAPI 서버 시작 실패! logs/fastapi.log 확인"
fi

if ps -p $CELERY_PID > /dev/null; then
    echo "✅ Celery Worker 정상 실행 중 (PID: $CELERY_PID)"
else
    echo "❌ Celery Worker 시작 실패! logs/celery.log 확인"
fi

if [ "$1" == "--with-flower" ] || [ "$1" == "-f" ]; then
    if ps -p $FLOWER_PID > /dev/null; then
        echo "✅ Flower 정상 실행 중 (PID: $FLOWER_PID)"
    else
        echo "❌ Flower 시작 실패! logs/flower.log 확인"
    fi
fi

echo ""
echo "💡 실시간 로그를 보려면: tail -f logs/*.log"
