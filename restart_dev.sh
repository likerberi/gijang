#!/bin/bash

# 개발 환경 재시작 스크립트

echo "🔄 개발 환경 재시작..."
echo ""

./stop_dev.sh
sleep 2
./start_dev.sh $@
