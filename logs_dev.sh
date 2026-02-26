#!/bin/bash

# 실시간 로그 확인 스크립트

echo "📊 실시간 로그 확인 (Ctrl+C로 종료)"
echo ""

# 모든 로그를 컬러로 출력
tail -f logs/fastapi.log logs/celery.log logs/flower.log 2>/dev/null | awk '
/fastapi/ {print "\033[32m" $0 "\033[0m"; next}
/celery/ {print "\033[33m" $0 "\033[0m"; next}
/flower/ {print "\033[35m" $0 "\033[0m"; next}
/ERROR|error|Error/ {print "\033[31m" $0 "\033[0m"; next}
/WARNING|warning|Warning/ {print "\033[33m" $0 "\033[0m"; next}
{print $0}
'
