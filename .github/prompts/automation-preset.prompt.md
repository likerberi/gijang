---
description: "웹 자동화 프리셋 JSON 생성. 자연어 설명을 automation/engine.py의 스텝 배열 JSON으로 변환. 홈택스, 카드사, 은행 등 반복 다운로드 작업 정의."
agent: "agent"
---

사용자가 자연어로 설명한 웹 반복작업을 automation 앱의 스텝 JSON으로 변환해줘.

## 지원 액션 (automation/engine.py)

| action | 설명 | selector 필요 | value 용도 |
|--------|------|:---:|---|
| `goto` | URL 이동 | ❌ | URL |
| `click` | 엘리먼트 클릭 | ✅ | - |
| `fill` | 입력 필드 채우기 | ✅ | 입력값 |
| `select_date` | 달력 UI에 날짜 입력 | ✅ | `{{date_from}}` 또는 `{{date_to}}` |
| `set_period` | 기간 버튼 클릭 | ✅ | - |
| `wait` | 대기 | ❌ | 밀리초 |
| `download` | 파일 다운로드 | ✅ | - |
| `screenshot` | 스크린샷 | ❌ | 파일명 |
| `scroll` | 스크롤 | ❌ | `down` 또는 `up` |
| `select_option` | 드롭다운 선택 | ✅ | 옵션값 |

## 템플릿 변수

| 변수 | 설명 |
|------|------|
| `{{date_from}}` | 조회 시작일 (YYYY-MM-DD) |
| `{{date_to}}` | 조회 종료일 (YYYY-MM-DD) |
| `{{year}}` | 연도 |
| `{{month}}` | 월 |

## 출력 형식

```json
{
  "name": "작업 이름",
  "target_url": "https://...",
  "login_required": true,
  "period_type": "1m",
  "download_format": "xlsx",
  "steps": [
    {"action": "goto", "value": "https://...", "description": "사이트 이동"},
    {"action": "click", "selector": "#menu", "description": "메뉴 클릭"},
    {"action": "select_date", "selector": "#startDate", "value": "{{date_from}}", "description": "시작일"},
    {"action": "select_date", "selector": "#endDate", "value": "{{date_to}}", "description": "종료일"},
    {"action": "click", "selector": "#btn-search", "description": "조회"},
    {"action": "wait", "value": "2000", "description": "결과 로딩 대기"},
    {"action": "download", "selector": "#btn-excel", "description": "엑셀 다운로드"}
  ]
}
```

## 기간 유형 (period_type)

| 값 | 설명 |
|----|------|
| `1d` | 1일 |
| `7d` | 1주일 |
| `1m` | 1개월 |
| `1y` | 1년 |
| `custom` | 사용자 지정 |

## 검증 규칙
- `click`, `fill`, `select_date`, `download`, `select_option` → selector 필수
- `fill` → value 필수
- `goto` → value(URL) 필수
- 마지막에 `download` 스텝 포함 권장
- 각 스텝에 한국어 `description` 포함

## 주의
- CSS selector는 사이트마다 다르므로, 실제 선택자가 불명확하면 placeholder(`#TODO-selector`)로 표시
- 로그인이 필요한 사이트는 `login_required: true` 명시
