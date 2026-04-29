document.addEventListener('DOMContentLoaded', () => {
  requireLogin();

  // 프로필 표시
  const user = getCurrentUser();
  const nicknameEl = document.getElementById('settings-nickname');
  if (nicknameEl && user) {
    nicknameEl.textContent = user.nickname;
  }

  // 나이대 드롭다운 — localStorage에서 불러와 초기값 세팅
  const ageSelect = document.getElementById('settings-age-group');
  if (ageSelect) {
    const saved = localStorage.getItem('gigi_age_group') || '';
    ageSelect.value = saved;
    ageSelect.addEventListener('change', () => {
      localStorage.setItem('gigi_age_group', ageSelect.value);
    });
  }


  // 글씨 크기 선택
  const savedStep = parseInt(localStorage.getItem('gigi_font_scale') ?? '2');
  document.querySelectorAll('.js-font-size').forEach((btn) => {
    const step = parseInt(btn.dataset.fontStep);
    if (step === savedStep) btn.classList.replace('btn-outline', 'btn-primary');
    btn.addEventListener('click', () => {
      document.querySelectorAll('.js-font-size').forEach((b) => b.classList.replace('btn-primary', 'btn-outline'));
      btn.classList.replace('btn-outline', 'btn-primary');
      setFontScale(step);
    });
  });

  // 비밀번호 변경 폼 토글
  const changeBtn  = document.getElementById('password-change-btn');
  const cancelBtn  = document.getElementById('password-cancel-btn');
  const form       = document.getElementById('password-change-form');

  changeBtn.addEventListener('click', () => {
    form.classList.remove('hidden');
    changeBtn.classList.add('hidden');
  });

  cancelBtn.addEventListener('click', () => {
    form.classList.add('hidden');
    changeBtn.classList.remove('hidden');
    document.getElementById('current-password').value = '';
    document.getElementById('new-password').value = '';
    document.getElementById('new-password-confirm').value = '';
    ['current-password-error', 'new-password-error', 'new-password-confirm-error'].forEach((id) => {
      const el = document.getElementById(id);
      el.textContent = '';
      el.classList.add('hidden');
    });
  });

  // 비밀번호 저장
  document.getElementById('password-save-btn').addEventListener('click', async () => {
    const currentPassword    = document.getElementById('current-password').value;
    const newPassword        = document.getElementById('new-password').value;
    const newPasswordConfirm = document.getElementById('new-password-confirm').value;

    ['current-password-error', 'new-password-error', 'new-password-confirm-error'].forEach((id) => {
      const el = document.getElementById(id);
      el.textContent = '';
      el.classList.add('hidden');
    });

    let hasError = false;

    if (!currentPassword) {
      const el = document.getElementById('current-password-error');
      el.textContent = '현재 비밀번호를 입력해주세요';
      el.classList.remove('hidden');
      hasError = true;
    }

    if (!newPassword) {
      const el = document.getElementById('new-password-error');
      el.textContent = '새 비밀번호를 입력해주세요';
      el.classList.remove('hidden');
      hasError = true;
    } else if (newPassword.length < 6) {
      const el = document.getElementById('new-password-error');
      el.textContent = '비밀번호는 6자 이상이어야 합니다';
      el.classList.remove('hidden');
      hasError = true;
    } else if (newPassword.length > 18) {
      const el = document.getElementById('new-password-error');
      el.textContent = '비밀번호는 18자 이하여야 합니다';
      el.classList.remove('hidden');
      hasError = true;
    }

    if (!newPasswordConfirm) {
      const el = document.getElementById('new-password-confirm-error');
      el.textContent = '새 비밀번호 확인을 입력해주세요';
      el.classList.remove('hidden');
      hasError = true;
    } else if (newPassword !== newPasswordConfirm) {
      const el = document.getElementById('new-password-confirm-error');
      el.textContent = '새 비밀번호가 일치하지 않습니다';
      el.classList.remove('hidden');
      hasError = true;
    }

    if (hasError) return;

    const saveBtn = document.getElementById('password-save-btn');
    saveBtn.disabled = true;
    saveBtn.textContent = '저장 중...';

    try {
      await apiPut('/auth/password', {
        current_password: currentPassword,
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      });
      showToast('비밀번호가 변경되었습니다.');
      cancelBtn.click();
    } catch (e) {
      const el = document.getElementById('current-password-error');
      el.textContent = e.message || '비밀번호 변경에 실패했습니다.';
      el.classList.remove('hidden');
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = '저장';
    }
  });

  document.querySelectorAll('.js-logout').forEach((button) => {
    button.addEventListener('click', logout);
  });

  // 회원탈퇴
  const deleteBtn = document.getElementById('delete-account-btn');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async () => {
      if (!confirm('정말 탈퇴하시겠습니까? 탈퇴 후에는 복구할 수 없습니다.')) return;

      deleteBtn.disabled = true;
      deleteBtn.textContent = '처리 중...';

      try {
        await apiDelete('/auth/me');
        logout();
      } catch (e) {
        showToast(e.message || '회원탈퇴에 실패했습니다.');
        deleteBtn.disabled = false;
        deleteBtn.textContent = '탈퇴하기';
      }
    });
  }
});
