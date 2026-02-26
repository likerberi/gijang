#!/bin/bash

# Flower 모니터링 도구 시작 스크립트

echo "🌸 Flower 모니터링 시작..."

# 가상 환경 활성화
source venv/bin/activate

# Flower 실행
celery -A fastapi_app.tasks.celery_app flower \
  --port=5555 \
  --basic_auth=admin:password123 \
  --broker=redis://localhost:6379/0 \
  --persistent=True \
  --db=flower.db

echo "Flower 접속: http://localhost:5555"
echo "인증정보: admin / password123"
