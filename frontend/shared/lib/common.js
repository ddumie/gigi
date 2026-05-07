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
  inviteSignup: '/pages/auth/invite-signup.html',
  onboard1:  '/pages/onboarding/step1-age.html',
  onboard2:  '/pages/onboarding/step2-fontsize.html',
  onboard3:  '/pages/onboarding/step3-interests.html',
  onboard4:  '/pages/onboarding/step4-ai.html',
  home:      '/pages/home/index.html',
  today:     '/pages/today/index.html',
  habits:    '/pages/habits/index.html',
  habitsAi:  '/pages/habits/ai-recommend.html',
  support:   '/pages/support/index.html',
  supportCreate: '/pages/support/create.html',
  supportManage: '/pages/support/manage.html',
  supportJoin:   '/pages/support/join.html',
  feed:      '/pages/neighbor/feed.html',
  feedDetail:'/pages/neighbor/feed-detail.html',
  groupSearch: '/pages/neighbor/group-search.html',
  groupSearchWrite: '/pages/neighbor/group-search-write.html',
  groupSearchEdit:  '/pages/neighbor/group-search-edit.html',
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

// ── 시간 포맷 공용 유틸 ──
// 단순 상대시간: "방금 전 / N분 전 / N시간 전 / N일 전"
function formatRelativeTime(isoString) {
  if (!isoString) return '';
  const then = new Date(isoString);
  const diffSec = Math.floor((Date.now() - then.getTime()) / 1000);
  if (diffSec < 60)    return '방금 전';
  if (diffSec < 3600)  return `${Math.floor(diffSec / 60)}분 전`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}시간 전`;
  return `${Math.floor(diffSec / 86400)}일 전`;
}

// 마지막 활동: 분/시간/오늘 오전·오후/어제/M월D일/1년 이상 전
function formatLastActivity(isoString) {
  if (!isoString) return '활동 기록 없음';
  const last = new Date(isoString);
  const now  = new Date();
  const diffMs = now - last;
  const diffMin  = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMs / 3600000);
  if (diffMin < 60)  return `${diffMin}분 전`;
  if (diffHour < 6)  return `${diffHour}시간 전`;
  if (last.toDateString() === now.toDateString()) {
    return last.getHours() < 12 ? '오늘 오전' : '오늘 오후';
  }
  const yesterday = new Date();
  yesterday.setDate(now.getDate() - 1);
  if (last.toDateString() === yesterday.toDateString()) return '어제';
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffDays >= 365) return '1년 이상 전';
  return `${last.getMonth() + 1}/${last.getDate()}`;
}

// ── 토스트 알림 ──
// showToast(msg)                              ─ 기본 3초
// showToast(msg, 5000)                        ─ 지속시간 ms (하위호환)
// showToast(msg, { duration, action: {label, onClick} }) ─ 액션 버튼 부착
function showToast(message, durationOrOpts = 3000) {
  const opts = typeof durationOrOpts === 'number'
    ? { duration: durationOrOpts }
    : (durationOrOpts || {});
  const duration = opts.duration ?? 3000;
  const action   = opts.action || null;

  let toast = document.getElementById('gigi-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'gigi-toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }

  // 기존 내용/타이머 초기화
  if (toast._timer) clearTimeout(toast._timer);
  toast.innerHTML = '';
  toast.classList.toggle('toast-with-action', !!action);

  const span = document.createElement('span');
  span.className = 'toast-message';
  span.textContent = message;
  toast.appendChild(span);

  if (action && typeof action.onClick === 'function') {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'toast-action';
    btn.textContent = action.label || '확인';
    btn.addEventListener('click', () => {
      try { action.onClick(); } catch (_) {}
      toast.classList.remove('show');
    });
    toast.appendChild(btn);
  }

  toast.classList.add('show');
  toast._timer = setTimeout(() => {
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
    `<a href="${PAGES[pageKey]}" data-nav="${sectionKey}" class="${section === sectionKey ? 'active' : ''}"
       onclick="if(!isLoggedIn()){event.preventDefault();window.location.href=PAGES.login;}">${label}</a>`;

  const header = document.createElement('header');
  header.className = 'gnb';
  header.innerHTML = `
    <a href="${PAGES.landing}" class="gnb-logo">지지</a>
    <nav class="gnb-nav">
      ${nav('home',     'home',     '홈')}
      ${nav('today',    'today',    '오늘')}
      ${nav('habits',   'habits',   '습관')}
      ${nav('support',  'support',  '모임')}
      ${nav('feed',     'neighbor', '이웃')}
      ${nav('settings', 'settings', '설정')}
    </nav>
    <div class="gnb-right">
      <span id="gnb-username" class="gnb-user">${nickname}</span>
      ${user ? '<button type="button" class="gnb-btn" onclick="logout()">로그아웃</button>' : ''}
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
