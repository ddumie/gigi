/* ============================================================
   홈 탭 — 받은 지지 / 조용한 모임원 / 이번 주 우리
   담당: 전연주
   ============================================================ */

const QUIET_THRESHOLD_MS = 3 * 24 * 60 * 60 * 1000; // 3일

const $greeting     = document.getElementById('home-greeting');
const $date         = document.getElementById('home-date');
const $receivedList = document.getElementById('received-support-list');
const $quietList    = document.getElementById('quiet-member-list');
const $weekly       = document.getElementById('weekly-summary');

let groupsCache = [];
let supportingKey = null; // `${groupId}:${userId}`

document.addEventListener('DOMContentLoaded', () => {
  requireLogin();

  // 신규 가입자(온보딩 미완료) → 온보딩으로 라우팅
  const user = getCurrentUser();
  if (user && user.is_first_login) {
    window.location.href = PAGES.onboard1;
    return;
  }

  initGreeting();
  loadAll();
});

function initGreeting() {
  const user = getCurrentUser();
  if (user) {
    $greeting.textContent = `안녕하세요, ${user.nickname}님`;
  }

  const now  = new Date();
  const days = ['일', '월', '화', '수', '목', '금', '토'];
  const y    = now.getFullYear();
  const m    = String(now.getMonth() + 1).padStart(2, '0');
  const d    = String(now.getDate()).padStart(2, '0');
  $date.textContent = `${y}.${m}.${d} ${days[now.getDay()]}`;
}

async function loadAll() {
  await Promise.all([loadReceivedSupport(), loadGroups()]);
}

// ── 카드1: 오늘 받은 지지 ──

async function loadReceivedSupport() {
  try {
    const data = await apiGet('/support/notifications/recent?limit=5');
    const items = data.notifications || [];

    if (items.length === 0) {
      $receivedList.innerHTML = `
        <div class="empty-state">
          아직 받은 지지가 없어요.<br>
          습관을 체크하면 모임원이 응원을 보낼 수 있어요.
        </div>`;
      return;
    }

    $receivedList.innerHTML = items.map(n => `
      <div class="home-item">
        <div class="home-item-main">
          <div class="home-item-title">${escapeHtml(n.content)}</div>
          <div class="home-item-meta">${formatRelativeTime(n.created_at)}</div>
        </div>
      </div>
    `).join('');

    if (items.some(n => !n.is_read)) {
      try {
        await apiPost('/support/notifications/read');
      } catch (_) {}
    }
  } catch (e) {
    $receivedList.innerHTML = '<p class="meta-text">불러오지 못했습니다.</p>';
  }
}

// ── 카드2 & 3: 모임 데이터 ──

async function loadGroups() {
  try {
    const data = await apiGet('/support/groups');
    groupsCache = data.groups || [];
    renderQuietMembers();
    renderWeeklySummary();
  } catch (e) {
    $quietList.innerHTML = '<p class="meta-text">불러오지 못했습니다.</p>';
    $weekly.innerHTML    = '<p class="meta-text">불러오지 못했습니다.</p>';
  }
}

function renderQuietMembers() {
  const me = getCurrentUser();
  const myId = me ? me.id : null;
  const now = Date.now();

  const candidates = [];
  groupsCache.forEach(({ group, members }) => {
    members.forEach(m => {
      if (m.user_id === myId) return;
      const lastMs = m.last_activity ? new Date(m.last_activity).getTime() : null;
      const isQuiet = lastMs === null || (now - lastMs) > QUIET_THRESHOLD_MS;
      if (isQuiet) {
        candidates.push({ group, member: m, lastMs });
      }
    });
  });

  // 가장 오래 무활동인 순
  candidates.sort((a, b) => {
    if (a.lastMs === null && b.lastMs === null) return 0;
    if (a.lastMs === null) return -1;
    if (b.lastMs === null) return 1;
    return a.lastMs - b.lastMs;
  });

  const top = candidates.slice(0, 5);

  if (top.length === 0) {
    $quietList.innerHTML = `
      <div class="empty-state">
        모임원 모두 활발히 활동 중이에요 👍
      </div>`;
    return;
  }

  $quietList.innerHTML = top.map(({ group, member }) => {
    const supportedToday = member.supported_today;
    const key = `${group.id}:${member.user_id}`;
    const isLoading = supportingKey === key;
    const btnLabel = supportedToday ? '지지 완료' : (isLoading ? '전송 중…' : '지지하기');
    const btnDisabled = supportedToday || isLoading ? 'disabled' : '';
    const btnClass = supportedToday ? 'btn btn-outline btn-sm' : 'btn btn-primary btn-sm';

    return `
      <div class="home-item">
        <div class="home-item-main">
          <div class="home-item-title">${escapeHtml(member.nickname || '모임원')}</div>
          <div class="home-item-meta">${escapeHtml(group.name)} · ${formatLastActivity(member.last_activity)}</div>
        </div>
        <div class="home-item-actions">
          <button
            type="button"
            class="${btnClass}"
            ${btnDisabled}
            onclick="sendHomeSupport(${group.id}, ${member.user_id})"
          >${btnLabel}</button>
        </div>
      </div>
    `;
  }).join('');
}

function renderWeeklySummary() {
  if (groupsCache.length === 0) {
    $weekly.innerHTML = `
      <div class="empty-state">
        아직 참여 중인 모임이 없어요.
      </div>`;
    return;
  }

  $weekly.innerHTML = groupsCache.map(({ group, members }) => {
    const memberCount = members.length;
    const avgRate = memberCount === 0
      ? 0
      : Math.round(members.reduce((sum, m) => sum + (m.complete_rate || 0), 0) / memberCount);

    return `
      <div class="home-summary-row">
        <strong>${escapeHtml(group.name)}</strong>
        <span class="home-item-meta">멤버 ${memberCount}명 · 🔥 ${group.streak}일</span>
        <span class="home-summary-value">${avgRate}%</span>
      </div>
    `;
  }).join('');
}

// ── 지지하기 (모임원 카드 + 조용한 모임원 카드 공통) ──

async function sendHomeSupport(groupId, toUserId) {
  const key = `${groupId}:${toUserId}`;
  if (supportingKey) return;
  supportingKey = key;
  renderQuietMembers();

  try {
    await apiPost(`/support/group/${groupId}/support/${toUserId}`, {});
    showToast('오늘의 지지를 보냈어요.');
    // 갱신
    await loadGroups();
  } catch (e) {
    showToast(e.message || '지지 전송에 실패했습니다.');
  } finally {
    supportingKey = null;
    renderQuietMembers();
  }
}

// ── 유틸 ──
// 시간 포맷은 common.js의 formatRelativeTime() / formatLastActivity() 사용

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}
