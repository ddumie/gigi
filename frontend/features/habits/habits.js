/* ============================================================
   습관 탭 — API 연동 + 동적 렌더링
   담당: 전연주
   ============================================================ */

// ── 상태 ──
let habits         = [];
let activeCategory = '';
let editingId      = null;

// ── DOM 참조 ──
const $list   = document.getElementById('habit-list');
const $count  = document.getElementById('habit-count');
const $btnAdd = document.getElementById('btn-add-habit');

// ── 요일 관련 상수 ──
const ALL_DAYS = ['월','화','수','목','금','토','일'];


// ── API 호출 ──

async function loadHabits() {
  try {
    const path = activeCategory
      ? `/habits/?category=${encodeURIComponent(activeCategory)}`
      : '/habits/';
    habits = await apiGet(path);
    render();
  } catch (e) {
    $list.innerHTML = '<p class="meta-text">습관을 불러오지 못했습니다.</p>';
  }
}

// ── 요일 피커 헬퍼 ──

function parseRepeatToDays(repeat) {
  if (!repeat || repeat === '매일') return [...ALL_DAYS];
  if (repeat === '평일') return ['월','화','수','목','금'];
  if (repeat === '주말') return ['토','일'];
  if (repeat === '주1회') return ['월'];
  if (repeat === '주3회') return ['월','수','금'];
  return ALL_DAYS.filter(d => repeat.includes(d));
}

function dayPickerHtml(containerId, currentRepeat) {
  const selected = parseRepeatToDays(currentRepeat);
  return `<div class="day-picker" id="${containerId}">${
    ALL_DAYS.map(d =>
      `<button type="button" class="day-btn${selected.includes(d) ? ' active' : ''}"
               data-day="${d}" onclick="toggleDay(this)">${d}</button>`
    ).join('')
  }</div>`;
}

function toggleDay(btn) {
  btn.classList.toggle('active');
}

function getRepeatFromDays(containerId) {
  const selected = [...document.querySelectorAll(`#${containerId} .day-btn.active`)]
    .map(b => b.dataset.day);
  if (selected.length === 0 || selected.length === 7) return '매일';
  if (selected.length === 5 && ['월','화','수','목','금'].every(d => selected.includes(d))) return '평일';
  if (selected.length === 2 && ['토','일'].every(d => selected.includes(d))) return '주말';
  return selected.join('') || '매일';
}


// ── 인라인 습관 추가 폼 ──

function openAddForm() {
  // 이미 열려 있으면 포커스만
  const existing = document.getElementById('habit-add-form');
  if (existing) {
    existing.querySelector('#add-title')?.focus();
    return;
  }
  // 편집 중인 카드 닫기
  document.querySelectorAll('.habit-row.editing').forEach(el => el.classList.remove('editing'));

  const formEl = document.createElement('article');
  formEl.className = 'card habit-add-form';
  formEl.id = 'habit-add-form';
  formEl.innerHTML = `
    <div class="habit-add-form-title">새 습관 추가</div>
    <input type="text" class="input edit-input" id="add-title" placeholder="습관 이름" maxlength="100">
    <select class="input" id="add-cat">
      <option value="운동">운동</option>
      <option value="복약">복약</option>
      <option value="식단">식단</option>
      <option value="수면">수면</option>
      <option value="기타">기타</option>
    </select>
    ${dayPickerHtml('add-days', '')}
    <div class="edit-actions">
      <button type="button" class="btn btn-primary btn-sm" onclick="submitAddForm()">저장</button>
      <button type="button" class="btn btn-outline btn-sm"  onclick="closeAddForm()">취소</button>
    </div>`;

  $list.prepend(formEl);
  document.getElementById('add-title')?.focus();
}

function closeAddForm() {
  document.getElementById('habit-add-form')?.remove();
}

async function submitAddForm() {
  const title      = document.getElementById('add-title')?.value.trim();
  const category   = document.getElementById('add-cat')?.value;
  const repeatType = getRepeatFromDays('add-days');

  if (!title) { showToast('습관 이름을 입력해주세요.'); return; }

  try {
    const res = await apiPost('/habits/', { title, category, repeat_type: repeatType });
    showToast('습관이 추가되었습니다.');
    if (res && res.is_first_habit) localStorage.setItem('gigi_show_first_habit_modal', 'true');
    closeAddForm();
    await loadHabits();
    showFirstHabitModalIfFlagged();
  } catch (e) {
    showToast(e.message || '저장에 실패했습니다.');
  }
}


// ── 카드 인라인 편집 ──

function openCardEdit(id) {
  // 이미 열린 편집 폼 닫기 (한 번에 하나만)
  document.querySelectorAll('.habit-row.editing').forEach(el => {
    el.classList.remove('editing');
  });
  const card = document.querySelector(`.habit-row[data-id="${id}"]`);
  if (!card) return;
  card.classList.add('editing');
  editingId = id;
}

async function saveCardEdit(id) {
  const title      = document.getElementById(`edit-title-${id}`)?.value.trim();
  const description = document.getElementById(`edit-desc-${id}`)?.value.trim() || null;
  const category   = document.getElementById(`edit-cat-${id}`)?.value;
  const repeatType = getRepeatFromDays(`edit-days-${id}`);

  if (!title) {
    showToast('습관 이름을 입력해주세요.');
    return;
  }

  try {
    await apiPut(`/habits/${id}`, {
      title,
      description,
      category,
      repeat_type: repeatType,
    });
    showToast('습관이 수정되었습니다.');
    editingId = null;
    await loadHabits();
  } catch (e) {
    showToast(e.message || '수정에 실패했습니다.');
  }
}

function cancelCardEdit(id) {
  const card = document.querySelector(`.habit-row[data-id="${id}"]`);
  if (card) card.classList.remove('editing');
  editingId = null;
}


// ── 첫 진입 모달 (첫 습관 등록 직후 1회 표시) ──

function showFirstHabitModalIfFlagged() {
  if (localStorage.getItem('gigi_show_first_habit_modal') !== 'true') return;

  const overlay = document.getElementById('first-habit-overlay');
  if (!overlay) return;

  overlay.classList.add('show');
  // 한 번만 표시 → 플래그 즉시 제거 (오늘 탭에서 중복 표시 방지)
  localStorage.removeItem('gigi_show_first_habit_modal');
}

async function deleteHabit(id) {
  if (!confirm('이 습관을 삭제할까요?')) return;
  try {
    await apiDelete(`/habits/${id}`);
    showToast('삭제되었습니다.');
    await loadHabits();
  } catch (e) {
    showToast(e.message || '삭제에 실패했습니다.');
  }
}

async function toggleVisibility(id) {
  try {
    const res = await apiPatch(`/habits/${id}/visibility`);
    showToast(res.is_hidden_from_group ? '모임에서 숨김 처리되었습니다.' : '모임에 공개되었습니다.');
    await loadHabits();
  } catch (e) {
    showToast(e.message || '변경에 실패했습니다.');
  }
}


// ── 렌더링 ──

function render() {
  $count.textContent = `총 ${habits.length}개의 습관이 등록되어 있어요`;

  if (habits.length === 0) {
    $list.innerHTML = `
      <div class="card habit-empty">
        <div class="habit-empty-emoji">🌱</div>
        <div class="habit-empty-title">첫 습관을 추가해보세요</div>
        <p class="meta-text">건강한 습관 하나가 건강한 하루를 만들어요</p>
      </div>`;
    return;
  }

  $list.innerHTML = habits.map(h => {
    const isGroup = h.group_id !== null;
    const isHidden = h.is_hidden_from_group;
    const badges  = [];

    badges.push(`<span class="badge badge-blue">${h.repeat_type}</span>`);
    if (h.is_ai_recommended) badges.push('<span class="badge badge-amber">AI</span>');
    if (isGroup)             badges.push('<span class="badge badge-green">모임</span>');
    if (isHidden)            badges.push('<span class="badge badge-gray">숨김</span>');

    const visibilityBtn = `<button class="btn btn-outline btn-sm" onclick="toggleVisibility(${h.id})">${isHidden ? '공개' : '숨기기'}</button>`;
    const safeTitle = h.title.replaceAll('"', '&quot;');

    return `
      <article class="card habit-row${isGroup ? ' is-group' : ''}" data-id="${h.id}">

        <!-- 뷰 모드 -->
        <div class="habit-card-view">
          <div class="habit-info">
            <div class="habit-title">${h.title}</div>
            ${h.description ? `<div class="habit-desc">${h.description}</div>` : ''}
            <div class="habit-sub">${h.repeat_type} · ${h.category}${isGroup ? ' · 모임 연동' : ''}</div>
          </div>
          <div class="habit-actions">
            ${badges.join('')}
            ${visibilityBtn}
            ${!isGroup ? `<button class="btn btn-outline btn-sm" onclick="openCardEdit(${h.id})">수정</button>
            <button class="btn btn-outline btn-sm" onclick="deleteHabit(${h.id})">삭제</button>` : ''}
          </div>
        </div>

        <!-- 편집 모드 (수정 클릭 시 카드 전체가 이 UI로 전환) -->
        ${!isGroup ? `
        <div class="habit-card-edit">
          <input type="text" class="input edit-input" id="edit-title-${h.id}"
                 value="${safeTitle}" placeholder="습관 이름">
          <input type="text" class="input edit-input" id="edit-desc-${h.id}"
                 value="${(h.description || '').replaceAll('"', '&quot;')}" placeholder="설명 (예: 매일 아침 7시, 10분 스트레칭)"
                 ${h.is_ai_recommended ? 'readonly' : ''}>
          <select class="input" id="edit-cat-${h.id}">
            <option value="운동"  ${h.category==='운동'  ? 'selected':''}>운동</option>
            <option value="복약"  ${h.category==='복약'  ? 'selected':''}>복약</option>
            <option value="식단"  ${h.category==='식단'  ? 'selected':''}>식단</option>
            <option value="수면"  ${h.category==='수면'  ? 'selected':''}>수면</option>
            <option value="기타"  ${h.category==='기타'  ? 'selected':''}>기타</option>
          </select>
          ${dayPickerHtml(`edit-days-${h.id}`, h.repeat_type)}
          <div class="edit-actions">
            <button class="btn btn-primary btn-sm" onclick="saveCardEdit(${h.id})">저장</button>
            <button class="btn btn-outline btn-sm" onclick="cancelCardEdit(${h.id})">취소</button>
          </div>
        </div>` : ''}

      </article>`;
  }).join('');
}


// ── 이벤트 바인딩 ──

document.addEventListener('DOMContentLoaded', () => {
  requireLogin();

  // 카테고리 필터
  document.querySelectorAll('[data-habit-filter]').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('[data-habit-filter]').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      activeCategory = chip.dataset.habitFilter;
      loadHabits();
    });
  });

  // 습관 추가 버튼
  $btnAdd.addEventListener('click', openAddForm);

  // 첫 진입 모달 닫기 버튼
  const dismissFirstModal = document.getElementById('dismiss-first-habit-modal');
  if (dismissFirstModal) {
    dismissFirstModal.addEventListener('click', () => {
      document.getElementById('first-habit-overlay').classList.remove('show');
    });
  }

  // 초기 로드
  loadHabits();
});
