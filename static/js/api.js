/**
 * DocMerge API Client
 * JWT 토큰 기반 API 통신 모듈
 */
const API = (() => {
  const TOKEN_KEY = 'docmerge_access';
  const REFRESH_KEY = 'docmerge_refresh';

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setTokens(access, refresh) {
    localStorage.setItem(TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  }

  function clearTokens() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  }

  function headers(extra = {}) {
    const h = {
      'Content-Type': 'application/json',
      ...extra,
    };
    const token = getToken();
    if (token) h['Authorization'] = `Bearer ${token}`;
    return h;
  }

  async function handleResponse(resp) {
    if (resp.status === 204) return null;

    let data;
    const ct = resp.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      data = await resp.json();
    } else {
      data = await resp.text();
    }

    if (!resp.ok) {
      // 401 → 토큰 갱신 시도
      if (resp.status === 401) {
        const refreshed = await tryRefresh();
        if (!refreshed) {
          clearTokens();
          window.location.href = '/accounts/login/';
          throw new Error('인증이 만료되었습니다');
        }
        // 갱신 성공했으면 caller가 재시도해야 하므로 에러 throw
        throw { retry: true };
      }

      // 에러 메시지 추출
      let msg = '요청 실패';
      if (typeof data === 'object') {
        if (data.detail) msg = data.detail;
        else if (data.error) msg = data.error;
        else {
          const first = Object.values(data)[0];
          msg = Array.isArray(first) ? first[0] : String(first);
        }
      } else {
        msg = data;
      }
      throw new Error(msg);
    }

    return data;
  }

  async function tryRefresh() {
    const refresh = localStorage.getItem(REFRESH_KEY);
    if (!refresh) return false;

    try {
      const resp = await fetch('/api/users/token/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });
      if (!resp.ok) return false;
      const data = await resp.json();
      setTokens(data.access, data.refresh || refresh);
      return true;
    } catch {
      return false;
    }
  }

  async function request(method, url, body, retried = false) {
    const opts = { method, headers: headers() };
    if (body && method !== 'GET') {
      opts.body = JSON.stringify(body);
    }
    try {
      const resp = await fetch(url, opts);
      return await handleResponse(resp);
    } catch (err) {
      if (err.retry && !retried) {
        return request(method, url, body, true);
      }
      throw err;
    }
  }

  async function login(username, password) {
    const resp = await fetch('/api/users/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.detail || data.error || '로그인 실패');
    }
    setTokens(data.access, data.refresh);
    return data;
  }

  async function register(username, email, password, password_confirm) {
    const resp = await fetch('/api/users/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password, password_confirm }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      let msg = '가입 실패';
      if (data.detail) msg = data.detail;
      else {
        const first = Object.values(data)[0];
        msg = Array.isArray(first) ? first[0] : String(first);
      }
      throw new Error(msg);
    }
    return data;
  }

  function logout() {
    clearTokens();
    window.location.href = '/accounts/login/';
  }

  // 파일 업로드 (multipart/form-data)
  async function upload(url, formData, retried = false) {
    const opts = {
      method: 'POST',
      headers: {},
      body: formData,
    };
    const token = getToken();
    if (token) opts.headers['Authorization'] = `Bearer ${token}`;
    // Content-Type은 FormData가 자동 설정

    try {
      const resp = await fetch(url, opts);
      return await handleResponse(resp);
    } catch (err) {
      if (err.retry && !retried) {
        return upload(url, formData, true);
      }
      throw err;
    }
  }

  return {
    getToken,
    setTokens,
    clearTokens,
    login,
    register,
    logout,
    refreshToken: tryRefresh,
    get:    (url) => request('GET', url),
    post:   (url, data) => request('POST', url, data),
    put:    (url, data) => request('PUT', url, data),
    patch:  (url, data) => request('PATCH', url, data),
    delete: (url) => request('DELETE', url),
    upload,
  };
})();
