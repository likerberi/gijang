#!/bin/bash
# 전체 시나리오 테스트 스크립트

echo "=== 📝 FastAPI 문서 처리 시나리오 테스트 ==="
echo ""

# 1. 로그인
echo "1️⃣  로그인 중..."
TOKEN=$(curl -s -X POST "http://localhost:8001/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123" | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

if [ -z "$TOKEN" ]; then
    echo "❌ 로그인 실패"
    exit 1
fi

echo "✅ 로그인 성공! 토큰: ${TOKEN:0:50}..."
echo ""

# 2. 파일 업로드
echo "2️⃣  Excel 파일 업로드 중..."
RESPONSE=$(curl -s -X POST "http://localhost:8001/api/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_document.xlsx" \
  -F "file_type=excel" \
  -F "title=직원 명단 테스트" \
  -F "description=Excel 파일 업로드 테스트")

echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

DOC_ID=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -z "$DOC_ID" ]; then
    echo "❌ 파일 업로드 실패"
    exit 1
fi

echo "✅ 파일 업로드 성공! 문서 ID: $DOC_ID"
echo ""

# 3. 문서 조회
echo "3️⃣  문서 정보 조회 중..."
sleep 2
curl -s -X GET "http://localhost:8001/api/documents/$DOC_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""

# 4. 처리될 때까지 대기
echo "4️⃣  문서 처리 중... (최대 30초 대기)"
for i in {1..10}; do
    STATUS=$(curl -s -X GET "http://localhost:8001/api/documents/$DOC_ID" \
      -H "Authorization: Bearer $TOKEN" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
    
    echo "   상태: $STATUS"
    
    if [ "$STATUS" = "completed" ]; then
        echo "✅ 문서 처리 완료!"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "❌ 문서 처리 실패"
        break
    fi
    
    sleep 3
done

echo ""

# 5. 추출된 데이터 조회
echo "5️⃣  추출된 데이터 조회..."
curl -s -X GET "http://localhost:8001/api/documents/$DOC_ID/extracted-data" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== ✅ 테스트 완료 ==="
