function togglePwVisibility(inputId, btn) {
  const input = document.getElementById(inputId);
  if (input.type === 'password') {
    input.type = 'text';
    btn.textContent = '숨기기';
  } else {
    input.type = 'password';
    btn.textContent = '보기';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  requireLogin();

  // 프로필 표시
  const user = getCurrentUser();
  const nicknameEl = document.getElementById('settings-nickname');
  if (nicknameEl && user) {
    nicknameEl.textContent = user.nickname;
  }

  // 나이대 + 건강관심사 API에서 가져오기
  const ageEl = document.getElementById('settings-age-group');
  apiGet('/auth/me').then((data) => {
    if (!data) return;
    if (ageEl) {
      ageEl.textContent = data.age_group || '-';
      if (data.age_group) localStorage.setItem('gigi_age_group', data.age_group);
    }
    const healthEl = document.getElementById('settings-health-interests');
    if (healthEl) healthEl.textContent = data.health_interests?.length ? data.health_interests.join(', ') : '-';
  }).catch(() => { showToast('프로필 정보를 불러오지 못했습니다.'); });

  // 나이대 변경 모달
  const ageEditBtn   = document.getElementById('age-group-edit-btn');
  const ageCancelBtn = document.getElementById('age-group-cancel-btn');
  const ageModal     = document.getElementById('age-group-modal');
  let selectedAge    = null;

  function openAgeModal() {
    selectedAge = null;
    document.querySelectorAll('.js-age-chip').forEach(c => {
      c.classList.remove('btn-primary');
      c.classList.add('btn-outline');
    });
    const errEl = document.getElementById('age-group-error');
    errEl.textContent = '';
    errEl.classList.add('hidden');
    ageModal.style.display = 'flex';
  }

  function closeAgeModal() {
    ageModal.style.display = 'none';
    selectedAge = null;
  }

  ageEditBtn.addEventListener('click', openAgeModal);
  ageCancelBtn.addEventListener('click', closeAgeModal);

  // 모달 바깥 클릭 시 닫기
  ageModal.addEventListener('click', (e) => {
    if (e.target === ageModal) closeAgeModal();
  });

  document.querySelectorAll('.js-age-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.js-age-chip').forEach(c => {
        c.classList.remove('btn-primary');
        c.classList.add('btn-outline');
      });
      chip.classList.remove('btn-outline');
      chip.classList.add('btn-primary');
      selectedAge = chip.dataset.value;
    });
  });

  document.getElementById('age-group-save-btn').addEventListener('click', async () => {
    const errEl = document.getElementById('age-group-error');
    errEl.textContent = '';
    errEl.classList.add('hidden');

    if (!selectedAge) {
      errEl.textContent = '나이대를 선택해주세요';
      errEl.classList.remove('hidden');
      return;
    }

    const saveBtn = document.getElementById('age-group-save-btn');
    saveBtn.disabled = true;
    saveBtn.textContent = '저장 중...';

    try {
      const res = await apiPatch('/auth/age-group', { age_group: selectedAge });
      if (ageEl) ageEl.textContent = res.age_group;
      localStorage.setItem('gigi_age_group', res.age_group);
      showToast('나이대가 변경되었습니다.');
      closeAgeModal();
    } catch (e) {
      errEl.textContent = e.message || '나이대 변경에 실패했습니다.';
      errEl.classList.remove('hidden');
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = '확인';
    }
  });

  // 닉네임 변경 모달
  const nicknameEditBtn   = document.getElementById('nickname-edit-btn');
  const nicknameCancelBtn = document.getElementById('nickname-cancel-btn');
  const nicknameModal     = document.getElementById('nickname-modal');

  function openNicknameModal() {
    document.getElementById('new-nickname').value = '';
    const errEl = document.getElementById('nickname-error');
    errEl.textContent = '';
    errEl.classList.add('hidden');
    nicknameModal.style.display = 'flex';
  }

  function closeNicknameModal() {
    nicknameModal.style.display = 'none';
  }

  nicknameEditBtn.addEventListener('click', openNicknameModal);
  nicknameCancelBtn.addEventListener('click', closeNicknameModal);

  nicknameModal.addEventListener('click', (e) => {
    if (e.target === nicknameModal) closeNicknameModal();
  });

  document.getElementById('nickname-save-btn').addEventListener('click', async () => {
    const newNickname = document.getElementById('new-nickname').value.trim();
    const errEl = document.getElementById('nickname-error');
    errEl.textContent = '';
    errEl.classList.add('hidden');

    if (!newNickname) {
      errEl.textContent = '닉네임을 입력해주세요';
      errEl.classList.remove('hidden');
      return;
    }
    if (newNickname.length < 2) {
      errEl.textContent = '닉네임은 2자 이상이어야 합니다';
      errEl.classList.remove('hidden');
      return;
    }
    if (newNickname.length > 12) {
      errEl.textContent = '닉네임은 12자 이하여야 합니다';
      errEl.classList.remove('hidden');
      return;
    }

    const saveBtn = document.getElementById('nickname-save-btn');
    saveBtn.disabled = true;
    saveBtn.textContent = '저장 중...';

    try {
      const res = await apiPatch('/auth/nickname', { nickname: newNickname });
      document.getElementById('settings-nickname').textContent = res.nickname;
      const storedUser = getCurrentUser();
      if (storedUser) {
        storedUser.nickname = res.nickname;
        setCurrentUser(storedUser);
      }
      showToast('닉네임이 변경되었습니다.');
      closeNicknameModal();
    } catch (e) {
      errEl.textContent = e.message || '닉네임 변경에 실패했습니다.';
      errEl.classList.remove('hidden');
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = '저장';
    }
  });

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
      document.getElementById('new-password').value = '';
      document.getElementById('new-password-confirm').value = '';
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
