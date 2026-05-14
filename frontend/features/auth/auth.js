// ── 비밀번호 보기/숨기기 ──
function togglePwVisibility(inputId, btn) {
  const input = document.getElementById(inputId);
  const reveal = input.type === 'password';
  input.type = reveal ? 'text' : 'password';
  btn.classList.toggle('is-revealed', reveal);
  btn.setAttribute('aria-label', reveal ? '비밀번호 숨기기' : '비밀번호 보기');
}

// ── 로그인 상태에서 auth 페이지 접근 차단 ──
if (isLoggedIn()) {
  window.location.href = PAGES.home;
}

// ── 공통 유틸 ──
function showError(id, message) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = message;
  el.classList.remove('hidden');
}

function clearError(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = '';
  el.classList.add('hidden');
}

function clearAllErrors(...ids) {
  ids.forEach(clearError);
}


// ── 회원가입 1단계 ──
const step1Next = document.getElementById('step1-next');
if (step1Next) {
  step1Next.addEventListener('click', async () => {
    const email    = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value;
    const confirm  = document.getElementById('signup-password-confirm').value;

    clearAllErrors('email-error', 'password-error', 'password-confirm-error');

    let hasError = false;

    if (!email) {
      showError('email-error', '이메일을 입력해주세요');
      hasError = true;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      showError('email-error', '올바른 이메일 형식이 아닙니다');
      hasError = true;
    }

    if (!password) {
      showError('password-error', '비밀번호를 입력해주세요');
      hasError = true;
    } else if (password.length < 6) {
      showError('password-error', '비밀번호는 6자 이상이어야 합니다');
      hasError = true;
    } else if (password.length > 18) {
      showError('password-error', '비밀번호는 18자 이하여야 합니다');
      hasError = true;
    }

    if (!confirm) {
      showError('password-confirm-error', '비밀번호 확인을 입력해주세요');
      hasError = true;
    } else if (password !== confirm) {
      showError('password-confirm-error', '비밀번호가 일치하지 않습니다');
      const pwInput = document.getElementById('signup-password');
      const pwConfirmInput = document.getElementById('signup-password-confirm');
      pwInput.value = '';
      pwConfirmInput.value = '';
      pwInput.type = 'password';
      pwConfirmInput.type = 'password';
      document.querySelectorAll('.pw-toggle-btn').forEach(btn => btn.classList.remove('is-revealed'));
      hasError = true;
    }

    if (hasError) return;

    // 이메일 중복 여부 비동기 확인
    step1Next.disabled = true;
    step1Next.textContent = '확인 중...';
    try {
      const result = await apiGet(`/auth/check/email?email=${encodeURIComponent(email)}`);
      if (!result.available) {
        showError('email-error', result.message || '이미 사용 중인 이메일입니다');
        step1Next.disabled = false;
        step1Next.textContent = '다음으로';
        return;
      }
    } catch (e) {
      showError('email-error', e.message || '이메일 확인에 실패했습니다');
      step1Next.disabled = false;
      step1Next.textContent = '다음으로';
      return;
    }

    sessionStorage.setItem('gigi_signup_email', email);
    sessionStorage.setItem('gigi_signup_password', password);
    window.location.href = PAGES.signup2;
  });
}


// ── 회원가입 2단계 ──
const step2Submit = document.getElementById('step2-submit');
if (step2Submit) {
  // 닉네임 추천
  const savedEmail = sessionStorage.getItem('gigi_signup_email') || '';
  const suggested  = savedEmail.split('@')[0] || '';
  const nicknameInput = document.getElementById('signup-nickname');
  const preview       = document.getElementById('nickname-preview');

  let trimmedSuggested = suggested.slice(0, 12);
  if (trimmedSuggested.length < 2) trimmedSuggested = trimmedSuggested + '1';
  if (trimmedSuggested && nicknameInput && !nicknameInput.value) {
    nicknameInput.value = trimmedSuggested;
  }
  if (preview) {
    preview.textContent = trimmedSuggested.length >= 2
      ? `추천 닉네임: ${trimmedSuggested}`
      : '이메일 앞부분을 추천 닉네임으로 보여줍니다.';
  }

  // 가입 완료 버튼
  step2Submit.addEventListener('click', async () => {
    const name     = document.getElementById('signup-name').value.trim();
    const nickname = nicknameInput ? nicknameInput.value.trim() : '';

    clearAllErrors('name-error', 'nickname-error');

    let hasError = false;

    if (!name) {
      showError('name-error', '이름을 입력해주세요');
      hasError = true;
    } else if (name.length < 2) {
      showError('name-error', '이름은 2자 이상이어야 합니다');
      hasError = true;
    } else if (name.length > 12) {
      showError('name-error', '이름은 12자 이하여야 합니다');
      hasError = true;
    }

    if (!nickname) {
      showError('nickname-error', '닉네임을 입력해주세요');
      hasError = true;
    } else if (nickname.length < 2) {
      showError('nickname-error', '닉네임은 2자 이상이어야 합니다');
      hasError = true;
    } else if (nickname.length > 12) {
      showError('nickname-error', '닉네임은 12자 이하여야 합니다');
      hasError = true;
    }

    if (hasError) return;

    const email    = sessionStorage.getItem('gigi_signup_email') || '';
    const password = sessionStorage.getItem('gigi_signup_password') || '';

    if (!email || !password) {
      showToast('입력 정보가 없습니다. 처음부터 다시 시도해주세요.');
      window.location.href = PAGES.signup1;
      return;
    }

    step2Submit.disabled = true;
    step2Submit.textContent = '가입 중...';

    try {
      const data = await apiPost('/auth/register', {
        email,
        password,
        password_confirm: password,
        name,
        nickname,
        profile_image: null,
      });

      setToken(data.access_token);
      setCurrentUser(data.user);

      sessionStorage.removeItem('gigi_signup_email');
      sessionStorage.removeItem('gigi_signup_password');

      const inviteCode = sessionStorage.getItem('gigi_invite_code');
      if (inviteCode) {
        sessionStorage.removeItem('gigi_invite_code');
        try {
          await apiPost(`/support/group/invite/${inviteCode}`);
        } catch (_) {
          // 모임 가입 실패해도 회원가입은 완료
        }
      }

      window.location.href = PAGES.signupDone;
    } catch (e) {
      step2Submit.disabled = false;
      step2Submit.textContent = '가입 완료';
      showToast(e.message || '회원가입에 실패했습니다.');
    }
  });
}


// ── 로그인 ──
const loginBtn = document.getElementById('login-submit');
if (loginBtn) {
  document.getElementById('login-password').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') loginBtn.click();
  });

  loginBtn.addEventListener('click', async () => {
    const email    = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    clearAllErrors('login-email-error', 'login-password-error');

    let hasError = false;

    if (!email) {
      showError('login-email-error', '이메일을 입력해주세요');
      hasError = true;
    }
    if (!password) {
      showError('login-password-error', '비밀번호를 입력해주세요');
      hasError = true;
    }

    if (hasError) return;

    loginBtn.disabled = true;
    loginBtn.textContent = '로그인 중...';

    try {
      const data = await apiPost('/auth/login', { email, password });

      setToken(data.access_token);
      setCurrentUser(data.user);

      window.location.href = PAGES.home;
    } catch (e) {
      loginBtn.disabled = false;
      loginBtn.textContent = '로그인';
      showError('login-password-error', e.message || '로그인에 실패했습니다.');
    }
  });
}


// ── 비밀번호 찾기 ──
const forgotSubmit = document.getElementById('forgot-submit');
if (forgotSubmit) {
  document.getElementById('forgot-email').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') forgotSubmit.click();
  });

  forgotSubmit.addEventListener('click', async () => {
    const email = document.getElementById('forgot-email').value.trim();
    clearError('forgot-email-error');

    if (!email) {
      showError('forgot-email-error', '이메일을 입력해주세요');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      showError('forgot-email-error', '올바른 이메일 형식이 아닙니다');
      return;
    }

    forgotSubmit.disabled = true;
    forgotSubmit.textContent = '발송 중...';

    try {
      await apiPost('/auth/forgot-password', { email });
      document.getElementById('forgot-form').classList.add('hidden');
      document.getElementById('forgot-success').classList.remove('hidden');
    } catch (e) {
      showError('forgot-email-error', e.message || '요청에 실패했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      forgotSubmit.disabled = false;
      forgotSubmit.textContent = '재설정 링크 받기';
    }
  });
}


// ── 비밀번호 재설정 ──
const resetSubmit = document.getElementById('reset-submit');
if (resetSubmit) {
  const params = new URLSearchParams(window.location.search);
  const resetToken = params.get('token');

  if (!resetToken) {
    document.getElementById('reset-form').classList.add('hidden');
    document.getElementById('reset-invalid').classList.remove('hidden');
  }

  resetSubmit.addEventListener('click', async () => {
    const newPassword        = document.getElementById('reset-new-password').value;
    const newPasswordConfirm = document.getElementById('reset-new-password-confirm').value;
    clearAllErrors('reset-new-password-error', 'reset-new-password-confirm-error');

    let hasError = false;

    if (!newPassword) {
      showError('reset-new-password-error', '새 비밀번호를 입력해주세요');
      hasError = true;
    } else if (newPassword.length < 6) {
      showError('reset-new-password-error', '비밀번호는 6자 이상이어야 합니다');
      hasError = true;
    } else if (newPassword.length > 18) {
      showError('reset-new-password-error', '비밀번호는 18자 이하여야 합니다');
      hasError = true;
    }

    if (!newPasswordConfirm) {
      showError('reset-new-password-confirm-error', '비밀번호 확인을 입력해주세요');
      hasError = true;
    } else if (newPassword !== newPasswordConfirm) {
      showError('reset-new-password-confirm-error', '비밀번호가 일치하지 않습니다');
      document.getElementById('reset-new-password').value = '';
      document.getElementById('reset-new-password-confirm').value = '';
      document.querySelectorAll('#reset-form .pw-toggle-btn').forEach(btn => btn.classList.remove('is-revealed'));
      hasError = true;
    }

    if (hasError) return;

    resetSubmit.disabled = true;
    resetSubmit.textContent = '변경 중...';

    try {
      await apiPost('/auth/reset-password', {
        token: resetToken,
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      });
      showToast('비밀번호가 변경되었습니다. 로그인해주세요.');
      setTimeout(() => { window.location.href = '/pages/auth/login.html'; }, 1500);
    } catch (e) {
      document.getElementById('reset-form').classList.add('hidden');
      document.getElementById('reset-invalid').classList.remove('hidden');
    } finally {
      resetSubmit.disabled = false;
      resetSubmit.textContent = '비밀번호 변경';
    }
  });
}


// ── 초대코드로 시작하기 ──
const inviteCodeInput = document.getElementById('invite-code');
const inviteSignupBtn = document.getElementById('invite-signup-btn');
if (inviteCodeInput && inviteSignupBtn) {
  inviteCodeInput.addEventListener('input', () => {
    inviteSignupBtn.disabled = inviteCodeInput.value.trim() === '';
  });

  inviteCodeInput.addEventListener('blur', async () => {
    const code = inviteCodeInput.value.trim();
    const summaryBox = document.getElementById('group-summary');
    const errorEl    = document.getElementById('invite-code-error');

    errorEl.textContent = '';
    errorEl.classList.add('hidden');
    summaryBox.style.display = 'none';
    inviteSignupBtn.disabled = true;

    if (!code) return;

    try {
      const res = await apiGet(`/support/group/summary/${code}`);
      document.getElementById('group-name').textContent    = res.name;
      document.getElementById('group-members').textContent = `멤버: ${res.members.join(', ')}`;
      summaryBox.style.display = 'block';
      inviteSignupBtn.disabled = false;
      inviteSignupBtn.dataset.inviteCode = code;
    } catch (e) {
      errorEl.textContent = '초대코드가 잘못되었거나 만료되었습니다.';
      errorEl.classList.remove('hidden');
    }
  });

  inviteSignupBtn.addEventListener('click', () => {
    const code = inviteSignupBtn.dataset.inviteCode;
    if (!code) return;
    sessionStorage.setItem('gigi_invite_code', code);
    window.location.href = PAGES.signup1;
  });
}
