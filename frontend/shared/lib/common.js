/* ============================================================
   지지(GIGI) 공통 JavaScript — UI 부트스트랩 + 전역 상태
   팀장(전연주) 작성 — 팀원은 shared/ 파일 수정 금지
   페이지별 추가 JS는 features/<도메인>/<도메인>.js 에 작성
   ============================================================ */

// ── 페이지 경로 중앙 관리 ──
const PAGES = {
  landing:   '/',
  login:     '/pages/auth/login.html',
  signup1:   '/pages/auth/signup-step1.html',
  signup2:   '/pages/auth/signup-step2.html',
  signupDone:'/pages/auth/signup-done.html',
  onboard1:  '/pages/onboarding/step1-age.html',
  onboard2:  '/pages/onboarding/step2-interests.html',
  onboard3:  '/pages/onboarding/step3-ai.html',
  today:     '/pages/today/index.html',
  habits:    '/pages/habits/index.html',
  support:   '/pages/support/index.html',
  supportCreate: '/pages/support/create.html',
  supportManage: '/pages/support/manage.html',
  feed:      '/pages/neighbor/feed.html',
  groupSearch: '/pages/neighbor/group-search.html',
  groupSearchWrite: '/pages/neighbor/group-search-write.html',
  groupSearchJoin:  '/pages/neighbor/group-search-join.html',
  myPosts:   '/pages/neighbor/my-posts.html',
  settings:  '/pages/settings/index.html',
};

// ── 사용자 세션 관리 ──
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

// ── 권한 체크 (페이지 접근 제어) ──
function requireLogin() {
  if (!isLoggedIn()) {
    window.location.href = PAGES.login;
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
  setFontScale(stepIndex);

  const slider = document.getElementById('font-scale-slider');
  if (slider) {
    slider.value = stepIndex;
    slider.addEventListener('input', (e) => setFontScale(Number(e.target.value)));
  }
}

function initActiveNav() {
  // initGnb()에서 active 클래스를 직접 설정하므로
  // 기존 HTML에 하드코딩된 헤더가 남아있는 페이지를 위한 폴백
  const section = document.body.dataset.section;
  if (!section) return;

  const navLinks = document.querySelectorAll('.gnb-nav a[data-nav]');
  navLinks.forEach((link) => {
    link.classList.toggle('active', link.dataset.nav === section);
  });
}

function initSelectableChips() {
  document.querySelectorAll('[data-chip-select]').forEach((chip) => {
    chip.addEventListener('click', () => {
      const group = chip.dataset.chipSelect;
      document.querySelectorAll(`[data-chip-select="${group}"]`).forEach((item) => {
        item.classList.remove('active');
      });
      chip.classList.add('active');
    });
  });
}

// ── 알림 폴링 ──
async function checkNotifications() {
  if (!isLoggedIn()) return;

  try {
    const data = await apiGet('/support/notifications/unread-count');
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

// ── GNB 동적 생성 + 초기화 ──
function initGnb() {
  // 이미 HTML에 <header class="gnb">가 있으면 제거 (중복 방지)
  const existing = document.querySelector('header.gnb');
  if (existing) existing.remove();

  const section  = document.body.dataset.section;
  const user     = getCurrentUser();
  const nickname = user ? user.nickname + '님' : '사용자님';

  const nav = (pageKey, sectionKey, label) =>
    `<a href="${PAGES[pageKey]}" data-nav="${sectionKey}" class="${section === sectionKey ? 'active' : ''}">${label}</a>`;

  const header = document.createElement('header');
  header.className = 'gnb';
  header.innerHTML = `
    <div class="gnb-logo">지지</div>
    <nav class="gnb-nav">
      ${nav('today',    'today',    '오늘')}
      ${nav('habits',   'habits',   '습관')}
      ${nav('support',  'support',  '지지')}
      ${nav('feed',     'neighbor', '이웃')}
      ${nav('settings', 'settings', '설정')}
    </nav>
    <div class="gnb-right">
      <span id="gnb-username" class="gnb-user">${nickname}</span>
      <div class="gnb-noti">
        <span id="noti-count" class="gnb-noti-badge"></span>
      </div>
    </div>
  `;

  document.body.prepend(header);
}

// ── 로그아웃 ──
function logout() {
  removeToken();
  localStorage.removeItem('gigi_user');
  window.location.href = PAGES.landing;
}

// ── 페이지 로드 시 공통 초기화 ──
document.addEventListener('DOMContentLoaded', () => {
  initFontScaler();
  initActiveNav();
  initSelectableChips();
  initGnb();

  // 로그인 상태면 30초마다 알림 체크
  if (isLoggedIn()) {
    checkNotifications();
    setInterval(checkNotifications, 30000);
  }
});
