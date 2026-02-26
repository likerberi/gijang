#!/bin/bash

# 개발 환경 종료 스크립트

echo "🛑 개발 환경 종료 중..."
echo ""

# PID 파일로 프로세스 종료
if [ -f .fastapi.pid ]; then
    PID=$(cat .fastapi.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo "✅ FastAPI 서버 종료 (PID: $PID)"
    fi
    rm .fastapi.pid
fi

if [ -f .celery.pid ]; then
    PID=$(cat .celery.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo "✅ Celery Worker 종료 (PID: $PID)"
    fi
    rm .celery.pid
fi

if [ -f .flower.pid ]; then
    PID=$(cat .flower.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo "✅ Flower 종료 (PID: $PID)"
    fi
    rm .flower.pid
fi

if [ -f .celery_django.pid ]; then
    PID=$(cat .celery_django.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo "✅ Django Celery Worker 종료 (PID: $PID)"
    fi
    rm .celery_django.pid
fi

if [ -f .django.pid ]; then
    PID=$(cat .django.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo "✅ Django 서버 종료 (PID: $PID)"
    fi
    rm .django.pid
fi

# 혹시 남아있는 프로세스 강제 종료
echo "🧹 남은 프로세스 정리..."
sleep 1
pkill -f "uvicorn fastapi_app" 2>/dev/null || true
pkill -f "celery.*fastapi_app" 2>/dev/null || true
pkill -f "celery.*config" 2>/dev/null || true
pkill -f "python manage.py runserver" 2>/dev/null || true

echo ""
echo "✅ 모든 서비스가 종료되었습니다"
echo ""
echo "💡 다시 시작하려면: ./start_dev.sh"
