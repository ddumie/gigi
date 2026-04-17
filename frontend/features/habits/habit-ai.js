/* ============================================================
   습관 탭 — AI 추천 기능 (온보딩 완료 후 추가 추천용)
   ============================================================ */

let currentHabits = [];
let currentInterests = [];

document.addEventListener('DOMContentLoaded', () => {
  requireLogin();

  // 관심사 칩 다중선택 (common.js 단일선택 동작을 교체)
  document.querySelectorAll('[data-chip-select="interest"]').forEach((chip) => {
    const fresh = chip.cloneNode(true);
    chip.replaceWith(fresh);
    fresh.addEventListener('click', () => fresh.classList.toggle('active'));
  });

  // AI 추천받기 버튼
  document.getElementById('btn-get-recommend').addEventListener('click', getRecommendations);

  // 등록 버튼
  document.getElementById('btn-select-habits').addEventListener('click', selectHabits);

  // 다시 추천받기 버튼
  document.getElementById('btn-retry').addEventListener('click', retryRecommendation);
});


// 관심사 선택 후 AI 추천 요청
async function getRecommendations() {
  const btn = document.getElementById('btn-get-recommend');
  currentInterests = [...document.querySelectorAll('[data-chip-select="interest"].active')]
    .map((c) => c.textContent.trim());

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
    await apiPost('/habits/ai-recommend/select', { selected_habits: selected });
    showToast('습관이 등록되었습니다.');
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
}
