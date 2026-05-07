/* ============================================================
   오늘 탭 — API 연동 + 동적 렌더링
   담당: 전연주
   ============================================================ */

// ── DOM 참조 ──
const $greeting   = document.getElementById('today-greeting');
const $date       = document.getElementById('today-date');
const $pill       = document.getElementById('today-pill');
const $checklist  = document.getElementById('today-checklist');
const $statRate   = document.getElementById('stat-rate');
const $statWeekly = document.getElementById('stat-weekly');
const $statStreak = document.getElementById('stat-streak');
const $statBadge  = document.getElementById('stat-badge');
const $calendar   = document.getElementById('mini-calendar');
const $notifSection = document.getElementById('notification-section');
const $notifList    = document.getElementById('notification-list');

let currentHabits = [];
let currentStats = null;
let openShareComposer = null;
let togglingHabitId = null;


// ── 초기화 ──

document.addEventListener('DOMContentLoaded', () => {
  requireLogin();
  initGreeting();
  initFirstLoginModal();
  loadDashboard();

  // 습관 추가 버튼 - 온보딩 여부에 따라 분기
  document.getElementById('btn-add-habit-today').addEventListener('click', () => {
    const user = getCurrentUser();
    if (user && user.is_first_login) {
      window.location.href = PAGES.onboard1;
    } else {
      window.location.href = PAGES.habits;
    }
  });
});


// ── 인사말 + 날짜 ──

function initGreeting() {
  const user = getCurrentUser();
  if (user) {
    $greeting.textContent = `안녕하세요, ${user.nickname}님`;
  }

  const now   = new Date();
  const days  = ['일', '월', '화', '수', '목', '금', '토'];
  const y     = now.getFullYear();
  const m     = String(now.getMonth() + 1).padStart(2, '0');
  const d     = String(now.getDate()).padStart(2, '0');
  $date.textContent = `${y}.${m}.${d} ${days[now.getDay()]}`;
}


// ── 대시보드 로드 ──

async function loadDashboard() {
  try {
    const data = await apiGet('/today/');
    currentHabits = data.habits;
    currentStats = data.stats;

    const stillChecked = openShareComposer && currentHabits.some(
      (habit) => habit.id === openShareComposer.habitId && habit.is_checked
    );
    if (!stillChecked) {
      openShareComposer = null;
    }

    renderChecklist(currentHabits, currentStats);
    renderStats(currentStats);
    renderCalendar(currentStats.monthly_progress || []);
  } catch (e) {
    $checklist.innerHTML = '<p class="meta-text">데이터를 불러오지 못했습니다.</p>';
  }

  await loadNotifications();
}


// ── 받은 지지 알림 ──
// 시간 포맷은 common.js의 formatRelativeTime() 사용

async function loadNotifications() {
  if (!$notifSection || !$notifList) return;

  try {
    const data = await apiGet('/support/notifications/recent?limit=3');
    const items = data.notifications || [];

    if (items.length === 0) {
      $notifSection.style.display = 'none';
      return;
    }

    $notifSection.style.display = '';
    $notifList.innerHTML = items.map(n => `
      <div class="notification-item" style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;padding:0.5rem 0;border-top:1px solid var(--color-border, #eee);">
        <span style="font-size:0.9rem;">${escapeHtml(n.content)}</span>
        <span class="meta-text" style="font-size:0.75rem;white-space:nowrap;">${formatRelativeTime(n.created_at)}</span>
      </div>
    `).join('');

    if (items.some(n => !n.is_read)) {
      try {
        await apiPost('/support/notifications/read');
      } catch (_) {}
    }
  } catch (e) {
    $notifSection.style.display = 'none';
  }
}


// ── 습관 체크리스트 ──

function renderChecklist(habits, stats) {
  $pill.textContent = `${stats.total_count}개 중 ${stats.checked_count}개 완료`;

  if (habits.length === 0) {
    $checklist.innerHTML = `
      <div style="text-align:center;padding:2rem 1rem;">
        <div style="font-size:1.5rem;margin-bottom:0.5rem;">🌱</div>
        <div style="font-size:0.9rem;font-weight:500;margin-bottom:0.4rem;">첫 습관을 추가해보세요</div>
        <div style="font-size:0.8rem;color:var(--color-text-s);line-height:1.7;">
          건강한 습관 하나가<br>건강한 하루를 만들어요
        </div>
      </div>`;
    return;
  }

  $checklist.innerHTML = habits.map(h => {
    const checked   = h.is_checked;
    const groupTag  = h.is_group ? '<span class="badge badge-green" style="margin-left:4px;">모임</span>' : '';
    const badgeText = checked ? '완료' : '미완료';
    const badgeCls  = checked ? 'badge-green' : 'badge-amber';
    const isShareOpen = openShareComposer?.habitId === h.id && checked;
    const habitTitle = escapeHtml(h.title);
    const category = escapeHtml(h.category);
    const repeatType = escapeHtml(h.repeat_type);

    return `
      <div class="today-habit-block" data-habit-id="${h.id}">
        <div class="checklist-item ${checked ? 'checked' : ''}" onclick="toggleCheck(${h.id})">
          <div class="check-box">${checked ? '✓' : ''}</div>
          <div style="flex:1;">
            <strong>${habitTitle}${groupTag}</strong>
            <p class="meta-text">${category} · ${repeatType}</p>
          </div>
          <span class="badge ${badgeCls}">${badgeText}</span>
        </div>
        ${isShareOpen ? renderShareComposer(h) : ''}
      </div>`;
  }).join('');
}


// ── 체크 토글 ──

async function toggleCheck(habitId) {
  if (togglingHabitId === habitId) return;
  togglingHabitId = habitId;

  try {
    const result = await apiPost(`/today/habits/${habitId}/toggle`, {});
    if (result?.is_checked) {
      openShareComposer = { habitId, draft: '' };
    } else if (openShareComposer?.habitId === habitId) {
      openShareComposer = null;
    }
    await loadDashboard();
  } catch (e) {
    showToast(e.message || '체크 변경에 실패했습니다.');
  } finally {
    togglingHabitId = null;
  }
}

function renderShareComposer(habit) {
  const draft = openShareComposer?.habitId === habit.id ? openShareComposer.draft : '';

  return `
    <div class="share-composer">
      <strong class="share-composer-title">이웃에 공유</strong>
      <p class="meta-text" style="margin-top:-0.2rem;">내가 한 습관을 남겨서 공유하거나 건너뛸 수 있어요.</p>
      <div style="display:flex;gap:0.5rem;align-items:center;">
        <textarea
          class="share-composer-input"
          rows="1"
          placeholder="(예시)시원한 물한잔 오늘도 완료!"
          oninput="updateShareDraft(${habit.id}, this.value)"
          style="flex:1;min-height:unset;height:2rem;font-size:0.8rem;padding:0.25rem 0.5rem;resize:none;"
        >${escapeHtml(draft)}</textarea>
        <button type="button" class="btn btn-primary btn-sm" onclick="submitNeighborShare(event, ${habit.id})">공유</button>
        <button type="button" class="btn btn-outline btn-sm" onclick="skipNeighborShare(event, ${habit.id})">건너뛰기</button>
      </div>
    </div>`;
}

function updateShareDraft(habitId, value) {
  if (openShareComposer?.habitId !== habitId) return;
  openShareComposer = { ...openShareComposer, draft: value };
}

async function submitNeighborShare(event, habitId) {
  event.stopPropagation();
  if (openShareComposer?.habitId !== habitId) return;

  try {
    const result = await apiPost('/today/share', {
      habit_id: habitId,
      content: openShareComposer.draft.trim(),
    });
    openShareComposer = null;
    const postId = result && result.id;
    showToast('이웃에 공유되었어요', {
      duration: 5000,
      action: postId ? {
        label: '확인하기',
        onClick: () => {
          window.location.href = `${PAGES.feedDetail}?post_id=${postId}`;
        },
      } : null,
    });
    await loadDashboard();
  } catch (e) {
    showToast(e.message || '공유에 실패했습니다.');
  }
}

function skipNeighborShare(event, habitId) {
  event.stopPropagation();
  if (openShareComposer?.habitId !== habitId) return;
  openShareComposer = null;
  renderChecklist(currentHabits, currentStats);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}


// ── 나의 현황 통계 ──

function renderStats(stats) {
  if (stats.total_count === 0) {
    $statRate.textContent   = '—';
    $statWeekly.textContent = '—';
    $statStreak.textContent = '—';
    return;
  }

  $statRate.textContent   = stats.completion_rate + '%';
  $statWeekly.textContent = stats.weekly_average + '%';
  $statStreak.textContent = stats.streak_days > 0
    ? stats.streak_days + '일 🔥'
    : '0일';
  // 칭호는 support 도메인 연동 후 업데이트 예정
}


// ── 미니 달력 ──

function renderCalendar(monthlyProgress) {
  const now   = new Date();
  const year  = now.getFullYear();
  const month = now.getMonth();
  const today = now.getDate();

  // 타이틀: 'X월 달성 현황'
  const $title = document.getElementById('calendar-title');
  if ($title) $title.textContent = `${month + 1}월 달성 현황`;

  const firstDay = new Date(year, month, 1).getDay();
  const lastDate = new Date(year, month + 1, 0).getDate();

  // day(1~31) → {checked, total} 맵 생성
  const progressMap = new Map();
  (monthlyProgress || []).forEach(p => {
    const day = new Date(p.date).getDate();
    progressMap.set(day, { checked: p.checked, total: p.total });
  });

  const dayLabels = ['일', '월', '화', '수', '목', '금', '토'];
  let html = dayLabels.map(d => `<span class="cal-hd">${d}</span>`).join('');

  // 빈 칸 (1일 시작 전)
  for (let i = 0; i < firstDay; i++) {
    html += '<span></span>';
  }

  // 날짜 셀
  for (let d = 1; d <= lastDate; d++) {
    const p       = progressMap.get(d) || { checked: 0, total: 0 };
    const ratio   = p.total > 0 ? Math.round(p.checked / p.total * 100) : 0;
    const isToday = d === today;
    const noHabit = p.total === 0;
    const classes = ['cal-cell'];
    if (isToday)   classes.push('today');
    if (ratio > 0) classes.push('has-progress');
    if (noHabit)   classes.push('no-habit');

    html += `<span class="${classes.join(' ')}"
                   data-day="${d}"
                   data-checked="${p.checked}"
                   data-total="${p.total}"
                   style="--fill:${ratio}%">
               <span class="cal-fill"></span>
               <span class="cal-num">${d}</span>
             </span>`;
  }

  $calendar.innerHTML = html;
}


// ── 달력 셀 클릭 시 'X/Y개 완료' 툴팁 ──

let activeTooltipDay = null;

function showCalTooltip(cell) {
  const tooltip = document.getElementById('cal-tooltip');
  if (!tooltip || !cell) return;

  const day     = cell.dataset.day;
  const checked = cell.dataset.checked || '0';
  const total   = cell.dataset.total || '0';

  tooltip.textContent = `${day}일 · ${checked}/${total}개 완료`;
  tooltip.classList.add('show');

  // 위치: 셀 상단 중앙 (status-calendar 기준 좌표)
  const container = tooltip.offsetParent || tooltip.parentElement;
  const cRect     = container.getBoundingClientRect();
  const rect      = cell.getBoundingClientRect();

  // 일단 중앙 정렬을 위해 width 측정
  tooltip.style.left = '0px';
  tooltip.style.top  = '0px';
  const tipW = tooltip.offsetWidth;
  const tipH = tooltip.offsetHeight;

  let left = rect.left - cRect.left + rect.width / 2 - tipW / 2;
  let top  = rect.top  - cRect.top  - tipH - 6;

  // 좌/우 가장자리 클램핑
  const maxLeft = container.clientWidth - tipW - 2;
  if (left < 2)        left = 2;
  if (left > maxLeft)  left = maxLeft;
  // 상단을 넘어가면 셀 아래로
  if (top < 0) top = rect.bottom - cRect.top + 6;

  tooltip.style.left = left + 'px';
  tooltip.style.top  = top + 'px';

  activeTooltipDay = day;
}

function hideCalTooltip() {
  const tooltip = document.getElementById('cal-tooltip');
  if (tooltip) tooltip.classList.remove('show');
  activeTooltipDay = null;
}

document.addEventListener('DOMContentLoaded', () => {
  if (!$calendar) return;

  // 셀 클릭 위임
  $calendar.addEventListener('click', (e) => {
    const cell = e.target.closest('.cal-cell');
    if (!cell) return;
    e.stopPropagation();
    // 습관 등록 전 날짜는 클릭 비활성화
    if (cell.classList.contains('no-habit')) {
      hideCalTooltip();
      return;
    }
    // 같은 셀 다시 클릭 시 닫기
    if (activeTooltipDay === cell.dataset.day) {
      hideCalTooltip();
    } else {
      showCalTooltip(cell);
    }
  });

  // 외부 클릭 시 닫기
  document.addEventListener('click', () => hideCalTooltip());
});


// ── 첫 진입 모달 (첫 습관 등록 직후 1회 표시) ──

function initFirstLoginModal() {
  const overlay    = document.getElementById('first-login-overlay');
  const dismiss    = document.getElementById('dismiss-first-login-modal');
  const shouldShow = localStorage.getItem('gigi_show_first_habit_modal') === 'true';

  if (overlay && shouldShow) {
    overlay.classList.add('show');
    // 한 번만 표시 → 플래그 즉시 제거
    localStorage.removeItem('gigi_show_first_habit_modal');
  }

  if (dismiss) {
    dismiss.addEventListener('click', () => {
      overlay.classList.remove('show');
    });
  }
}
