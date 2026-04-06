/* ============================================================
   지지(GIGI) 공통 JavaScript
   팀장(전연주) 작성 — 팀원은 이 파일 수정하지 말 것
   페이지별 추가 JS는 js/pages/ 에 작성
   ============================================================ */

// ── API 기본 설정 ──
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

function getCurrentUser() {
  const user = localStorage.getItem('gigi_user');
  return user ? JSON.parse(user) : null;
}

function setCurrentUser(user) {
  localStorage.setItem('gigi_user', JSON.stringify(user));
}

function isLoggedIn() {
  return !!getToken();
}

function isSenior() {
  const user = getCurrentUser();
  return user && user.account_type === 'senior';
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

  if (response.status === 401) {
    removeToken();
    localStorage.removeItem('gigi_user');
    window.location.href = '/html/login.html';
    return;
  }

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '요청에 실패했습니다.');
  }

  return await response.json();
}

// 편의 함수
const apiGet = (path) => api('GET', path);
const apiPost = (path, body) => api('POST', path, body);
const apiPut = (path, body) => api('PUT', path, body);
const apiDelete = (path) => api('DELETE', path);

// ── 권한 체크 (페이지 접근 제어) ──
function requireLogin() {
  if (!isLoggedIn()) {
    window.location.href = '/html/login.html';
  }
}

function requireSenior() {
  requireLogin();
  if (!isSenior()) {
    alert('시니어 계정만 이용할 수 있는 기능입니다.');
    window.location.href = '/html/home.html';
  }
}

// ── 글씨 크기 조절 ──
const FONT_STEPS = [80, 90, 100, 110, 120, 130, 150];

function setFontScale(stepIndex) {
  const percent = FONT_STEPS[stepIndex];
  document.documentElement.style.fontSize = (16 * percent / 100) + 'px';
  localStorage.setItem('gigi_font_scale', stepIndex);

  const label = document.getElementById('font-scale-value');
  if (label) {
    label.textContent = percent === 100 ? '기본' : percent + '%';
  }
}

function initFontScaler() {
  const saved = localStorage.getItem('gigi_font_scale');
  const stepIndex = saved !== null ? Number(saved) : 2; // 기본 100%

  const slider = document.getElementById('font-scale-slider');
  if (slider) {
    slider.value = stepIndex;
    setFontScale(stepIndex);
    slider.addEventListener('input', (e) => setFontScale(Number(e.target.value)));
  }
}

// ── 알림 폴링 ──
async function checkNotifications() {
  if (!isLoggedIn()) return;

  try {
    const data = await apiGet('/groups/notifications/unread-count');
    const badge = document.getElementById('noti-count');
    if (badge) {
      if (data.count > 0) {
        badge.textContent = data.count;
        badge.style.display = 'flex';
      } else {
        badge.style.display = 'none';
      }
    }
  } catch (e) {
    // 알림 조회 실패 시 무시
  }
}

// ── 토스트 알림 ──
function showToast(message, duration = 3000) {
  let toast = document.getElementById('gigi-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'gigi-toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }

  toast.textContent = message;
  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
  }, duration);
}

// ── GNB 권한별 메뉴 분기 ──
function initGnb() {
  const user = getCurrentUser();
  if (!user) return;

  // 커뮤니티 메뉴: 가족 계정은 숨김 (URL 직접 접근은 API에서 차단)
  const communityNav = document.querySelector('[data-page="community"]');
  if (communityNav && user.account_type === 'family') {
    communityNav.classList.add('hidden');
  }

  // 사용자 이름 표시
  const userLabel = document.getElementById('gnb-username');
  if (userLabel) {
    userLabel.textContent = user.nickname + '님';
  }
}

// ── 로그아웃 ──
function logout() {
  removeToken();
  localStorage.removeItem('gigi_user');
  window.location.href = '/';
}

// ── 페이지 로드 시 공통 초기화 ──
document.addEventListener('DOMContentLoaded', () => {
  initFontScaler();
  initGnb();

  // 로그인 상태면 30초마다 알림 체크
  if (isLoggedIn()) {
    checkNotifications();
    setInterval(checkNotifications, 30000);
  }
});