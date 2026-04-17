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
      hasError = true;
    }

    if (hasError) return;

    // 이메일 중복 여부 비동기 확인
    step1Next.disabled = true;
    step1Next.textContent = '확인 중...';
    try {
      const result = await apiPost('/auth/check/email', { email });
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

  if (suggested && nicknameInput && !nicknameInput.value) {
    nicknameInput.value = suggested;
  }
  if (preview) {
    preview.textContent = suggested
      ? `추천 닉네임: ${suggested}`
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

      window.location.href = PAGES.today;
    } catch (e) {
      loginBtn.disabled = false;
      loginBtn.textContent = '로그인';
      showError('login-password-error', e.message || '로그인에 실패했습니다.');
    }
  });
}
