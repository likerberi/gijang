#!/bin/bash
# 자동화 기능 테스트 시나리오
# Usage: bash test_automation.sh

set -e

BASE="http://localhost:8000"

echo "=== 1. 로그인 ==="
RESP=$(curl -s -X POST "$BASE/api/users/login/" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test1234"}')
TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")
AUTH="Authorization: Bearer $TOKEN"
echo "Token obtained"

echo ""
echo "=== 2. 프리셋 목록 조회 ==="
curl -s -H "$AUTH" "$BASE/api/automation/tasks/presets/" | \
  python3 -c "import sys,json; data=json.load(sys.stdin); [print(f'  [{i+1}] {p[\"name\"]} ({len(p[\"steps\"])} steps)') for i,p in enumerate(data)]"

echo ""
echo "=== 3. 작업 생성 (은행 프리셋 기반) ==="
TASK=$(curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "name": "테스트 — 거래내역 다운로드",
    "target_url": "https://httpbin.org/html",
    "period_type": "1m",
    "download_format": "xlsx",
    "steps": [
      {"action": "goto", "value": "https://httpbin.org/html", "description": "테스트 페이지 이동"},
      {"action": "wait", "value": "1000", "description": "로딩 대기"},
      {"action": "screenshot", "selector": "", "description": "스크린샷"}
    ]
  }' "$BASE/api/automation/tasks/")
TASK_ID=$(echo "$TASK" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Task created: id=$TASK_ID"

echo ""
echo "=== 4. 작업 상세 조회 ==="
curl -s -H "$AUTH" "$BASE/api/automation/tasks/$TASK_ID/" | \
  python3 -c "
import sys,json
d = json.load(sys.stdin)
print(f'  Name: {d[\"name\"]}')
print(f'  URL: {d[\"target_url\"]}')
print(f'  Period: {d[\"period_display\"]}')
print(f'  Status: {d[\"status_display\"]}')
print(f'  Steps (JSON): {len(d.get(\"steps\",[]))}')
print(f'  Steps (DB): {len(d.get(\"step_list\",[]))}')
"

echo ""
echo "=== 5. 스텝 저장 (DB 모델로) ==="
curl -s -X PUT -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {"action": "goto", "selector": "", "value": "https://httpbin.org/html", "wait_after": 500, "description": "페이지 이동"},
      {"action": "wait", "selector": "", "value": "1000", "wait_after": 0, "description": "로딩 대기"},
      {"action": "screenshot", "selector": "", "value": "", "wait_after": 500, "description": "스크린샷 캡처"}
    ]
  }' "$BASE/api/automation/tasks/$TASK_ID/update_steps/" | \
  python3 -c "import sys,json; data=json.load(sys.stdin); print(f'  Saved {len(data)} steps')"

echo ""
echo "=== 6. 드라이런 ==="
curl -s -H "$AUTH" "$BASE/api/automation/tasks/$TASK_ID/dry_run/" | \
  python3 -c "
import sys,json
d = json.load(sys.stdin)
print(f'  Task: {d[\"task_name\"]}')
print(f'  Date range: {d[\"date_range\"][\"from\"]} ~ {d[\"date_range\"][\"to\"]}')
print(f'  Steps: {d[\"total_steps\"]}')
v = d['validation']
if v['valid']:
    print('  ✅ Validation passed')
else:
    for issue in v['issues']:
        print(f'  ⚠️ {issue}')
"

echo ""
echo "=== 7. 실행 (Playwright 필요 — 미설치 시 실패 예상) ==="
RUN=$(curl -s -X POST -H "$AUTH" "$BASE/api/automation/tasks/$TASK_ID/run/")
echo "$RUN" | python3 -c "
import sys,json
d = json.load(sys.stdin)
print(f'  Status: {d[\"status\"]}')
print(f'  Duration: {d.get(\"duration_ms\", \"N/A\")}ms')
if d.get('error_message'):
    print(f'  Error: {d[\"error_message\"][:100]}')
if d.get('log'):
    print(f'  Log entries: {len(d[\"log\"])}')
"

echo ""
echo "=== 8. 실행 기록 조회 ==="
curl -s -H "$AUTH" "$BASE/api/automation/tasks/$TASK_ID/runs/" | \
  python3 -c "
import sys,json
data = json.load(sys.stdin)
for r in data:
    print(f'  Run #{r[\"id\"]}: {r[\"status\"]} ({r.get(\"duration_ms\",\"?\")}ms)')
"

echo ""
echo "=== 9. 작업 목록 조회 ==="
curl -s -H "$AUTH" "$BASE/api/automation/tasks/" | \
  python3 -c "
import sys,json
data = json.load(sys.stdin)
tasks = data if isinstance(data, list) else data.get('results', [])
for t in tasks:
    print(f'  [{t[\"id\"]}] {t[\"name\"]} — {t[\"status_display\"]} ({t.get(\"step_count\",0)} steps, {t.get(\"run_count\",0)} runs)')
"

echo ""
echo "=== 10. 정리 (테스트 작업 삭제) ==="
curl -s -X DELETE -H "$AUTH" "$BASE/api/automation/tasks/$TASK_ID/" -o /dev/null -w "HTTP %{http_code}"
echo ""
echo ""
echo "=== 테스트 완료 ==="
