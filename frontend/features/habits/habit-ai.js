/* ============================================================
   습관 탭 — AI 추천 기능 (온보딩 완료 후 추가 추천용)
   ============================================================ */

let currentHabits = [];
let currentInterests = [];
let customInterests = []; // 직접 입력한 관심사

document.addEventListener('DOMContentLoaded', () => {
  requireLogin();

  // 관심사 칩 다중선택 (common.js 단일선택 동작을 교체)
  document.querySelectorAll('[data-chip-select="interest"]').forEach((chip) => {
    const fresh = chip.cloneNode(true);
    chip.replaceWith(fresh);
    fresh.addEventListener('click', () => fresh.classList.toggle('active'));
  });

  // 직접 입력 - 엔터
  const customInput = document.getElementById('custom-interest-input');
  customInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); addCustomInterest(); }
  });
  // 직접 입력 - 추가 버튼
  document.getElementById('btn-add-custom').addEventListener('click', addCustomInterest);

  // AI 추천받기 버튼
  document.getElementById('btn-get-recommend').addEventListener('click', getRecommendations);

  // 등록 버튼
  document.getElementById('btn-select-habits').addEventListener('click', selectHabits);

  // 다시 추천받기 버튼
  document.getElementById('btn-retry').addEventListener('click', retryRecommendation);

  // 온보딩에서 저장한 관심사 자동 선택
  loadSavedInterests();
});


async function loadSavedInterests() {
  try {
    const pref = await apiGet('/onboarding/preferences');
    const saved = pref.health_interests || [];
    if (!saved.length) return;

    document.querySelectorAll('[data-chip-select="interest"]').forEach((chip) => {
      if (saved.includes(chip.textContent.trim())) {
        chip.classList.add('active');
      }
    });
  } catch (_) {
    // 저장한 관심사 조회 실패 시 칩은 비선택 상태로 유지(그냥 사용자가 선택하면됨)
  }
}


// 직접 입력 관심사 추가
function addCustomInterest() {
  const input = document.getElementById('custom-interest-input');
  const value = input.value.trim();
  if (!value) return;
  if (customInterests.includes(value)) {
    showToast('이미 추가된 항목이에요.');
    return;
  }
  customInterests.push(value);
  renderCustomTags();
  input.value = '';
}

// 직접 입력 태그 렌더링
function renderCustomTags() {
  const container = document.getElementById('custom-tags');
  container.innerHTML = customInterests.map((tag, i) => `
    <span class="chip active" style="display:inline-flex;align-items:center;gap:0.25rem;">
      ${tag}
      <button onclick="removeCustomTag(${i})" style="background:none;border:none;cursor:pointer;font-size:0.9rem;line-height:1;">✕</button>
    </span>
  `).join('');
}

// 직접 입력 태그 삭제
function removeCustomTag(index) {
  customInterests.splice(index, 1);
  renderCustomTags();
}


// 관심사 선택 후 AI 추천 요청
async function getRecommendations() {
  const btn = document.getElementById('btn-get-recommend');
  const chipInterests = [...document.querySelectorAll('[data-chip-select="interest"].active')]
    .map((c) => c.textContent.trim());
  currentInterests = [...chipInterests, ...customInterests];

  if (!currentInterests.length) {
    showToast('관심사를 하나 이상 선택해주세요.');
    return;
  }

  btn.disabled = true;
  btn.textContent = '추천 받는 중...';

  try {
    const result = await apiPost('/habits/ai-recommend', { health_interests: currentInterests });
    currentHabits = result.habits || [];
    renderResult(currentHabits);
    showStep('result');
  } catch (err) {
    if (err.message === '온보딩을 먼저 완료해주세요.') {
      showToast('온보딩을 먼저 완료해주세요. 온보딩 페이지로 이동합니다.');
      setTimeout(() => {
        window.location.href = PAGES.onboard1 + '?returnTo=' + encodeURIComponent(window.location.pathname);
      }, 1500);
      return;
    }
    showToast(err.message);
    btn.disabled = false;
    btn.textContent = '맞춤 습관 추천받기';
  }
}


// 다시 추천받기
async function retryRecommendation() {
  const btn = document.getElementById('btn-retry');
  btn.disabled = true;
  btn.textContent = '추천 받는 중...';

  try {
    const result = await apiPost('/habits/ai-recommend', { health_interests: currentInterests });
    currentHabits = result.habits || [];
    renderResult(currentHabits);
  } catch (err) {
    showToast(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = '다시 추천받기';
  }
}


// 선택한 습관 등록
async function selectHabits() {
  const btn = document.getElementById('btn-select-habits');
  const selected = [...document.querySelectorAll('.recommendation-card.active')]
    .map((card) => currentHabits[parseInt(card.dataset.index)]);

  if (!selected.length) {
    showToast('습관을 하나 이상 선택해주세요.');
    return;
  }

  btn.disabled = true;
  btn.textContent = '등록 중...';

  try {
    const res = await apiPost('/habits/ai-recommend/select', { selected_habits: selected });
    showToast('습관이 등록되었습니다.');

    // 서버가 판단한 첫 습관 여부 → 모달 플래그 저장 후 습관 탭에서 표시
    if (res && res.is_first_habit) {
      localStorage.setItem('gigi_show_first_habit_modal', 'true');
    }
    window.location.href = PAGES.habits;
  } catch (err) {
    showToast(err.message);
    btn.disabled = false;
    btn.textContent = '선택한 습관 등록하기';
  }
}


// 추천 결과 카드 렌더링
function renderResult(habits) {
  const list = document.getElementById('recommendation-list');
  list.innerHTML = habits.map((h, i) => `
    <article class="recommendation-card" data-index="${i}" style="cursor:pointer;">
      <strong>${h.title}</strong>
      <p class="meta-text">${h.description}</p>
    </article>
  `).join('');

  // 이벤트 위임: list에 한 번만 등록
  list.onclick = (e) => {
    const card = e.target.closest('.recommendation-card');
    if (card) card.classList.toggle('active');
  };
}


// step 전환
function showStep(step) {
  document.getElementById('step-interests').style.display = step === 'interests' ? '' : 'none';
  document.getElementById('step-result').style.display = step === 'result' ? '' : 'none';

  if (step === 'interests') {
    const btn = document.getElementById('btn-get-recommend');
    btn.disabled = false;
    btn.textContent = '나의 맞춤 습관 추천받기';
  }
}
