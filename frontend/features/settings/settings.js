document.addEventListener('DOMContentLoaded', () => {
  // 닉네임 표시
  const user = getCurrentUser();
  const nicknameEl = document.getElementById('settings-nickname');
  if (nicknameEl && user) {
    nicknameEl.textContent = user.nickname;
  }

  document.querySelectorAll('.js-logout').forEach((button) => {
    button.addEventListener('click', logout);
  });
});
