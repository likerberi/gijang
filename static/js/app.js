/**
 * DocMerge 공통 유틸리티
 */

// === 헬퍼 함수 ===

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function statusBadge(status) {
  const map = {
    uploaded:    ['업로드됨', 'badge-gray'],
    processing:  ['처리중', 'badge-info'],
    completed:   ['완료', 'badge-success'],
    failed:      ['실패', 'badge-danger'],
    pending:     ['대기중', 'badge-warning'],
  };
  const [label, cls] = map[status] || [status || '-', 'badge-gray'];
  return `<span class="badge ${cls}">${label}</span>`;
}

function formatSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let size = bytes;
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024;
    i++;
  }
  return `${size.toFixed(i > 0 ? 1 : 0)} ${units[i]}`;
}

function formatDate(isoStr) {
  if (!isoStr) return '-';
  const d = new Date(isoStr);
  if (isNaN(d)) return isoStr;
  const Y = d.getFullYear();
  const M = String(d.getMonth() + 1).padStart(2, '0');
  const D = String(d.getDate()).padStart(2, '0');
  const h = String(d.getHours()).padStart(2, '0');
  const m = String(d.getMinutes()).padStart(2, '0');
  return `${Y}-${M}-${D} ${h}:${m}`;
}

function docTypeBadge(t) {
  const map = {
    excel: ['Excel', 'badge-success'],
    pdf:   ['PDF', 'badge-danger'],
    image: ['이미지', 'badge-info'],
  };
  const [label, cls] = map[t] || [t || '-', 'badge-gray'];
  return `<span class="badge ${cls}">${label}</span>`;
}

// === 모달 ===

function showModal(title, bodyHtml, footerHtml) {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-body').innerHTML = bodyHtml || '';
  document.getElementById('modal-footer').innerHTML = footerHtml || '';
  document.getElementById('modal-overlay').style.display = 'flex';
}

function closeModal() {
  document.getElementById('modal-overlay').style.display = 'none';
  document.getElementById('modal-body').innerHTML = '';
  document.getElementById('modal-footer').innerHTML = '';
}

// === 토스트 ===

function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity .3s';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// === 초기화 (base.html 로드 시) ===

document.addEventListener('DOMContentLoaded', () => {
  // 모달 닫기
  const modalClose = document.getElementById('modal-close');
  const modalOverlay = document.getElementById('modal-overlay');
  if (modalClose) modalClose.addEventListener('click', closeModal);
  if (modalOverlay) {
    modalOverlay.addEventListener('click', (e) => {
      if (e.target === modalOverlay) closeModal();
    });
  }

  // 사이드바 토글 (모바일)
  const menuToggle = document.getElementById('menu-toggle');
  const sidebar = document.getElementById('sidebar');
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    // 메인 클릭 시 닫기
    const main = document.querySelector('.main-content');
    if (main) {
      main.addEventListener('click', () => sidebar.classList.remove('open'));
    }
  }

  // 사용자 정보 로드
  const token = API.getToken();
  if (token) {
    loadUserInfo();
    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
      btnLogout.style.display = 'block';
      btnLogout.addEventListener('click', () => {
        API.logout();
      });
    }
  }
});

async function loadUserInfo() {
  try {
    const data = await API.get('/api/users/me/');
    const nameEl = document.getElementById('user-name');
    if (nameEl) nameEl.textContent = data.username || data.email || '사용자';
  } catch {
    // 실패 시 무시
  }
}
