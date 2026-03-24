---
name: template-page
description: "프론트엔드 페이지 추가 스킬. USE FOR: 새 HTML 템플릿 페이지 생성, base.html 상속, 사이드바 메뉴 등록, API 연동 패턴 적용. 기장 프로젝트의 프론트엔드 컨벤션을 자동 적용."
---

# Template Page

기장 프로젝트에 새 프론트엔드 페이지를 추가할 때 사용합니다.

## When to Use
- 새 페이지(화면)를 추가할 때
- 기존 페이지와 동일한 스타일/구조로 만들어야 할 때

## 템플릿 구조

### base.html 상속 패턴
```html
{% extends 'base.html' %}

{% block title %}페이지 제목{% endblock %}
{% block nav_mypage %}active{% endblock %}

{% block content %}
<div class="page-header">
  <h2>📋 페이지 제목</h2>
  <p class="page-desc">설명 텍스트</p>
</div>

<div class="content-card">
  <!-- 본문 -->
</div>

<!-- 모달 (필요시) -->
<div class="modal-overlay" id="myModal" style="display:none;">
  <div class="modal">
    <div class="modal-header">
      <h3>모달 제목</h3>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div class="modal-body" id="modalBody">
    </div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', () => {
  loadData();
});

async function loadData() {
  try {
    const res = await API.get('/api/myapp/items/');
    renderList(res);
  } catch (e) {
    console.error(e);
  }
}
</script>
{% endblock %}
```

### API 호출 패턴 (static/js/api.js 사용)
```javascript
// GET 요청
const data = await API.get('/api/endpoint/');

// POST 요청
const result = await API.post('/api/endpoint/', { key: 'value' });

// PUT 요청
await API.put(`/api/endpoint/${id}/`, payload);

// DELETE 요청
await API.delete(`/api/endpoint/${id}/`);

// 파일 업로드
const formData = new FormData();
formData.append('file', fileInput.files[0]);
const res = await API.upload('/api/endpoint/', formData);

// 파일 다운로드
await API.download(`/api/endpoint/${id}/download/`, 'filename.xlsx');
```

### 공통 UI 컴포넌트 (CSS 클래스)

| 클래스 | 용도 |
|--------|------|
| `.page-header` | 페이지 상단 제목 영역 |
| `.content-card` | 카드형 컨테이너 |
| `.btn`, `.btn-primary`, `.btn-danger`, `.btn-ghost` | 버튼 |
| `.btn-sm` | 작은 버튼 |
| `.table` | 테이블 |
| `.badge`, `.badge-success`, `.badge-warning`, `.badge-danger` | 상태 뱃지 |
| `.modal-overlay`, `.modal`, `.modal-header`, `.modal-body` | 모달 |
| `.form-group`, `.form-label`, `.form-input`, `.form-select` | 폼 요소 |
| `.alert`, `.alert-info`, `.alert-warning`, `.alert-danger` | 알림 |
| `.stats-grid`, `.stat-card`, `.stat-value`, `.stat-label` | 통계 카드 |
| `.empty-state` | 빈 상태 안내 |

### 상태 뱃지 패턴
```javascript
function statusBadge(status) {
  const map = {
    'pending': '<span class="badge badge-warning">대기</span>',
    'processing': '<span class="badge badge-info">처리중</span>',
    'completed': '<span class="badge badge-success">완료</span>',
    'failed': '<span class="badge badge-danger">실패</span>',
  };
  return map[status] || `<span class="badge">${status}</span>`;
}
```

### 테이블 렌더링 패턴
```javascript
function renderTable(items) {
  const html = `
    <table class="table">
      <thead>
        <tr>
          <th>이름</th>
          <th>상태</th>
          <th>생성일</th>
          <th>작업</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(item => `
          <tr>
            <td>${item.name}</td>
            <td>${statusBadge(item.status)}</td>
            <td>${new Date(item.created_at).toLocaleDateString('ko-KR')}</td>
            <td>
              <button class="btn btn-sm" onclick="viewDetail(${item.id})">상세</button>
              <button class="btn btn-sm btn-danger" onclick="deleteItem(${item.id})">삭제</button>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
  document.getElementById('tableContainer').innerHTML = html;
}
```

## Procedure

1. `templates/<pagename>.html` 생성 (base.html 상속)
2. `config/frontend_views.py` → 뷰 함수 추가
3. `config/urls.py` → 프론트엔드 라우트 추가 + import 추가
4. `templates/base.html` → 사이드바 `<nav>` 에 메뉴 항목 추가
5. 템플릿 내 `{% block nav_<pagename> %}active{% endblock %}` 으로 사이드바 활성화
6. API 호출은 `API.get()` / `API.post()` 등 사용 (JWT 자동 처리)

## 주의사항
- 인라인 스크립트는 `{% block extra_js %}` 안에
- 날짜 포맷: `toLocaleDateString('ko-KR')`
- 금액 포맷: `toLocaleString('ko-KR')` + '원'
- 삭제 시 `confirm()` 확인 필수
- 빈 데이터일 때 `.empty-state` 표시
