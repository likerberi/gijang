#!/bin/bash

# 서비스 종료 스크립트

echo "🛑 서비스 종료 중..."

if [ -f fastapi.pid ]; then
    PID=$(cat fastapi.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "✅ FastAPI 서버 종료 (PID: $PID)"
    fi
    rm fastapi.pid
fi

if [ -f celery.pid ]; then
    PID=$(cat celery.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "✅ Celery Worker 종료 (PID: $PID)"
    fi
    rm celery.pid
fi

if [ -f flower.pid ]; then
    PID=$(cat flower.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "✅ Flower 모니터링 종료 (PID: $PID)"
    fi
    rm flower.pid
fi

# 남은 프로세스 강제 종료
pkill -f "uvicorn fastapi_app"
pkill -f "celery.*fastapi_app"

echo "✅ 모든 서비스가 종료되었습니다"
