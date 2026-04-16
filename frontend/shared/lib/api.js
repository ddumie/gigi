/* ============================================================
   지지(GIGI) API 통신 모듈
   팀장(전연주) 작성 — 팀원은 shared/ 파일 수정 금지
   ============================================================ */

const API_BASE = '/api/v1';

// ── JWT 토큰 관리 ──
function getToken() {
  return localStorage.getItem('gigi_token');
}

function setToken(token) {
  localStorage.setItem('gigi_token', token);
}

function removeToken() {
  localStorage.removeItem('gigi_token');
}

// ── API 호출 래퍼 ──
async function api(method, path, body = null) {
  const options = {
    method: method,
    headers: { 'Content-Type': 'application/json' },
  };

  const token = getToken();
  if (token) {
    options.headers['Authorization'] = 'Bearer ' + token;
  }

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(API_BASE + path, options);

  // 401 → 토큰 만료/미인증 → 로그인 페이지로 이동
  // 단, 로그인/회원가입 요청은 예외 (각 페이지에서 에러 메시지 표시)
  const isAuthRequest = path.startsWith('/auth/login') || path.startsWith('/auth/register');
  if (response.status === 401 && !isAuthRequest) {
    removeToken();
    localStorage.removeItem('gigi_user');
    window.location.href = PAGES.login;
    return;
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || '요청에 실패했습니다.');
  }

  return await response.json();
}

// 편의 함수
const apiGet = (path) => api('GET', path);
const apiPost = (path, body) => api('POST', path, body);
const apiPut = (path, body) => api('PUT', path, body);
const apiDelete = (path) => api('DELETE', path);
