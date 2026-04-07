document.addEventListener('DOMContentLoaded', () => {
  const signupEmail = document.getElementById('signup-email');
  const nicknameInput = document.getElementById('signup-nickname');
  const preview = document.getElementById('nickname-preview');

  if (signupEmail) {
    signupEmail.addEventListener('input', (event) => {
      localStorage.setItem('gigi_signup_email', event.target.value.trim());
    });
  }

  if (nicknameInput) {
    const savedEmail = localStorage.getItem('gigi_signup_email') || '';
    const suggested = savedEmail.split('@')[0] || '';

    if (suggested && !nicknameInput.value) {
      nicknameInput.value = suggested;
    }

    if (preview) {
      preview.textContent = suggested ? `추천 닉네임: ${suggested}` : '이메일 앞부분을 추천 닉네임으로 보여줍니다.';
    }
  }
});
