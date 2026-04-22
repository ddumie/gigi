document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;

  if (path.includes('step1-age')) {
    initStep1();
  } else if (path.includes('step2-interests')) {
    initStep2();
  } else if (path.includes('step3-ai')) {
    initStep3();
  }
});

// Step1: 나이대 선택
function initStep1() {
  const nextBtn = document.querySelector('.btn-ai');
  if (!nextBtn) return;

  nextBtn.addEventListener('click', (e) => {
    e.preventDefault();
    const selected = document.querySelector('[data-chip-select="age-group"].active');
    if (selected) {
      localStorage.setItem('gigi_age_group', selected.textContent.trim());
    }
    window.location.href = PAGES.onboard2;
  });
}

// Step2: 관심사 선택
function initStep2() {
  // common.js의 단일선택 동작을 다중선택으로 교체(선호도는 여러개 선택이 가능함)
  document.querySelectorAll('[data-chip-select="interest"]').forEach((chip) => {
    const fresh = chip.cloneNode(true);
    chip.replaceWith(fresh);
    fresh.addEventListener('click', () => fresh.classList.toggle('active'));
  });

  const recommendBtn = document.querySelector('.btn-ai');
  if (!recommendBtn) return;

  // AI 추천받기 버튼 클릭 → preferences 저장 → ai-recommend 호출 → step3 이동
  recommendBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    recommendBtn.disabled = true;
    recommendBtn.textContent = '추천 받는 중...';
    // 선택한 나이대랑 관심사 수집하고
    const ageGroup = localStorage.getItem('gigi_age_group') || null;
    const interests = [...document.querySelectorAll('[data-chip-select="interest"].active')]
      .map((c) => c.textContent.trim());

    try {
      // preferences 저장
      await apiPost('/onboarding/preferences', {
        age_group: ageGroup,
        health_interests: interests,
      });
      // ai-recommend 호출 → localStorage 저장 → step3 이동
      const result = await apiPost('/onboarding/ai-recommend');
      if (!result) return; // 401 등으로 이미 리다이렉트된 경우
      localStorage.setItem('gigi_ai_habits', JSON.stringify(result)); //결과 저장
      window.location.href = PAGES.onboard3;
    } catch (err) {
      showToast(err.message);
      recommendBtn.disabled = false;
      recommendBtn.textContent = 'AI 습관 추천받기';
    }
  });
}

// Step3: AI 추천 습관 선택
function initStep3() {
  const stored = localStorage.getItem('gigi_ai_habits');
  if (!stored || stored === 'undefined') {
    showToast('추천 정보를 불러올 수 없습니다. 다시 시도해주세요.');
    window.location.href = PAGES.onboard2;
    return;
  }

  const data = JSON.parse(stored);
  const habits = data.habits || [];

  // localStorage에서 habits 꺼내서 카드 렌더링
  const list = document.querySelector('.recommendation-list');
  list.innerHTML = habits.map((h, i) => `
    <article class="recommendation-card" data-index="${i}">
      <strong>${h.title}</strong>
      <p class="meta-text">${h.description}</p>
    </article>
  `).join('');

  // 카드 클릭 토글
  list.querySelectorAll('.recommendation-card').forEach((card) => {
    card.addEventListener('click', () => card.classList.toggle('active'));
  });

  // 다시 추천받기 버튼
  const retryBtn = [...document.querySelectorAll('.btn-outline')]
    .find((btn) => btn.href && btn.href.includes('step3'));

  if (retryBtn) {
    if (!data.can_retry) {
      retryBtn.style.display = 'none'; //can_retry(재추천)값이 False인경우는 버튼숨김(재추천 횟수소진 완료상태)
    } else {
      retryBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        retryBtn.disabled = true;
        retryBtn.textContent = '추천 받는 중...';
        try {
          const result = await apiPost('/onboarding/ai-recommend');
          localStorage.setItem('gigi_ai_habits', JSON.stringify(result));
          location.reload();
        } catch (err) {
          showToast(err.message);
          retryBtn.disabled = false;
          retryBtn.textContent = '다시 추천받기';
        }
      });
    }
  }

  // 등록 버튼 클릭 → select API 호출 → today 이동
  const submitBtn = document.querySelector('.btn-primary');
  if (!submitBtn) return;

  submitBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    const selected = [...document.querySelectorAll('.recommendation-card.active')]
      .map((card) => habits[parseInt(card.dataset.index)]);

    if (!selected.length) {
      showToast('습관을 하나 이상 선택해주세요.');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = '등록 중...';
    
    try {
      const res = await apiPost('/onboarding/ai-recommend/select', { selected_habits: selected });
      localStorage.removeItem('gigi_ai_habits');
      localStorage.removeItem('gigi_age_group');

      // 서버가 판단한 첫 습관 여부 → today 탭 진입 시 모달 표시
      if (res && res.is_first_habit) {
        localStorage.setItem('gigi_show_first_habit_modal', 'true');
      }
      window.location.href = PAGES.today;
    } catch (err) {
      showToast(err.message);
      submitBtn.disabled = false;
      submitBtn.textContent = '선택한 습관 등록하고 시작하기';
    }
  });
}
