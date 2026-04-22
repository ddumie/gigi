/* ============================================================
   습관 탭 — API 연동 + 동적 렌더링
   담당: 전연주
   ============================================================ */

// ── 상태 ──
let habits         = [];
let activeCategory = '';   // '' = 전체
let editingId      = null; // null = 추가 모드, 숫자 = 수정 모드

// ── DOM 참조 ──
const $list         = document.getElementById('habit-list');
const $count        = document.getElementById('habit-count');
const $modal        = document.getElementById('habit-modal');
const $modalTitle   = document.getElementById('modal-title');
const $inputTitle   = document.getElementById('modal-habit-title');
const $inputCat     = document.getElementById('modal-habit-category');
const $inputTime    = document.getElementById('modal-habit-time');
const $inputRepeat  = document.getElementById('modal-habit-repeat');
const $btnAdd       = document.getElementById('btn-add-habit');
const $btnSave      = document.getElementById('modal-save');
const $btnCancel    = document.getElementById('modal-cancel');


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

async function saveHabit() {
  const title      = $inputTitle.value.trim();
  const category   = $inputCat.value;
  const time       = $inputTime.value || null;
  const repeatType = $inputRepeat.value;

  if (!title) {
    showToast('습관 이름을 입력해주세요.');
    return;
  }

  try {
    if (editingId) {
      await apiPut(`/habits/${editingId}`, {
        title,
        category,
        time,
        repeat_type: repeatType,
      });
      showToast('습관이 수정되었습니다.');
    } else {
      const res = await apiPost('/habits/', {
        title,
        category,
        time,
        repeat_type: repeatType,
      });
      showToast('습관이 추가되었습니다.');

      // 서버가 판단한 첫 습관 여부 → 모달 플래그 저장
      if (res && res.is_first_habit) {
        localStorage.setItem('gigi_show_first_habit_modal', 'true');
      }
    }
    closeModal();
    await loadHabits();

    // 첫 습관 등록인 경우 현재 페이지(습관 탭)에서도 모달 즉시 표시
    showFirstHabitModalIfFlagged();
  } catch (e) {
    showToast(e.message || '저장에 실패했습니다.');
  }
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
      <div class="card" style="text-align:center;padding:2rem 1rem;">
        <div style="font-size:1.5rem;margin-bottom:0.5rem;">🌱</div>
        <div style="font-size:0.9rem;font-weight:500;margin-bottom:0.4rem;">첫 습관을 추가해보세요</div>
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

    return `
      <article class="card habit-row" data-id="${h.id}" ${isGroup ? 'style="border-color:var(--color-success);"' : ''}>
        <div class="habit-info">
          <div class="habit-title">${h.title}</div>
          <div class="habit-sub">${h.repeat_type} ${h.time ? '· ' + h.time : ''} · ${h.category}${isGroup ? ' · 모임 연동' : ''}</div>
        </div>
        <div style="display:flex;align-items:center;gap:0.25rem;">
          ${badges.join('')}
          ${visibilityBtn}
          ${!isGroup ? `<button class="btn btn-outline btn-sm" onclick="openEditModal(${h.id})">수정</button>
          <button class="btn btn-outline btn-sm" onclick="deleteHabit(${h.id})">삭제</button>` : ''}
        </div>
      </article>`;
  }).join('');
}


// ── 모달 ──

function openAddModal() {
  editingId          = null;
  $modalTitle.textContent = '습관 추가';
  $inputTitle.value  = '';
  $inputCat.value    = '운동';
  $inputTime.value   = '';
  $inputRepeat.value = '매일';
  $modal.style.display = 'flex';
}

function openEditModal(id) {
  const habit = habits.find(h => h.id === id);
  if (!habit) return;

  editingId          = id;
  $modalTitle.textContent = '습관 수정';
  $inputTitle.value  = habit.title;
  $inputCat.value    = habit.category;
  $inputTime.value   = habit.time || '';
  $inputRepeat.value = habit.repeat_type;
  $modal.style.display = 'flex';
}

function closeModal() {
  $modal.style.display = 'none';
  editingId = null;
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

  // 모달 버튼
  $btnAdd.addEventListener('click', openAddModal);
  $btnSave.addEventListener('click', saveHabit);
  $btnCancel.addEventListener('click', closeModal);

  // 모달 바깥 클릭 시 닫기
  $modal.addEventListener('click', (e) => {
    if (e.target === $modal) closeModal();
  });

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
