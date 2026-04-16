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
const $groupSum   = document.getElementById('group-summary');


// ── 초기화 ──

document.addEventListener('DOMContentLoaded', () => {
  requireLogin();
  initGreeting();
  initFirstLoginModal();
  loadDashboard();
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
    renderChecklist(data.habits, data.stats);
    renderStats(data.stats);
    renderCalendar(data.stats.weekly_checked_dates);
    renderGroupSummary();
  } catch (e) {
    $checklist.innerHTML = '<p class="meta-text">데이터를 불러오지 못했습니다.</p>';
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
        <div style="font-size:0.8rem;color:var(--color-text-s);margin-bottom:1.2rem;line-height:1.7;">
          건강한 습관 하나가<br>건강한 하루를 만들어요
        </div>
        <a href="${PAGES.onboard1}" class="btn btn-ai btn-full" style="margin-bottom:0.4rem;">AI 습관 추천받기</a>
        <a href="${PAGES.habits}" class="btn btn-outline btn-full btn-sm">직접 습관 추가하기</a>
      </div>`;
    return;
  }

  $checklist.innerHTML = habits.map(h => {
    const checked   = h.is_checked;
    const groupTag  = h.is_group ? '<span class="badge badge-green" style="margin-left:4px;">모임</span>' : '';
    const badgeText = checked ? '완료' : '미완료';
    const badgeCls  = checked ? 'badge-green' : 'badge-amber';

    return `
      <div class="checklist-item ${checked ? 'checked' : ''}" data-habit-id="${h.id}" onclick="toggleCheck(${h.id})">
        <div class="check-box">${checked ? '✓' : ''}</div>
        <div style="flex:1;">
          <strong>${h.title}${groupTag}</strong>
          <p class="meta-text">${h.category} · ${h.repeat_type}${h.time ? ' · ' + h.time : ''}</p>
        </div>
        <span class="badge ${badgeCls}">${badgeText}</span>
      </div>`;
  }).join('');
}


// ── 체크 토글 ──

async function toggleCheck(habitId) {
  try {
    await apiPost(`/today/habits/${habitId}/toggle`, {});
    await loadDashboard();
  } catch (e) {
    showToast(e.message || '체크 변경에 실패했습니다.');
  }
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

function renderCalendar(checkedDates) {
  const now   = new Date();
  const year  = now.getFullYear();
  const month = now.getMonth();
  const today = now.getDate();

  const firstDay   = new Date(year, month, 1).getDay();
  const lastDate   = new Date(year, month + 1, 0).getDate();
  const checkedSet = new Set(checkedDates.map(d => new Date(d).getDate()));

  const dayLabels = ['일', '월', '화', '수', '목', '금', '토'];
  let html = dayLabels.map(d => `<span class="cal-hd">${d}</span>`).join('');

  // 빈 칸 (1일 시작 전)
  for (let i = 0; i < firstDay; i++) {
    html += '<span></span>';
  }

  // 날짜
  for (let d = 1; d <= lastDate; d++) {
    const isDone  = checkedSet.has(d);
    const isToday = d === today;
    let cls = '';
    if (isDone)  cls = 'done';
    if (isToday) cls += ' today';
    html += `<span class="${cls.trim()}">${d}</span>`;
  }

  $calendar.innerHTML = html;
}


// ── 모임 요약 (support 연동 전 placeholder) ──

function renderGroupSummary() {
  // TODO: support 도메인 API 연동 후 모임 멤버 달성률 표시
  $groupSum.textContent = '아직 속한 모임이 없어요';
}


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
