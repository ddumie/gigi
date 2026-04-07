document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.checklist-item').forEach((item) => {
    item.addEventListener('click', () => {
      item.classList.toggle('checked');
    });
  });

  const modal = document.getElementById('first-login-modal');
  const dismissButton = document.getElementById('dismiss-first-login-modal');
  const user = getCurrentUser();

  if (modal && user && user.is_first_login) {
    modal.classList.add('show');
  }

  if (dismissButton) {
    dismissButton.addEventListener('click', () => {
      modal.classList.remove('show');
      if (user) {
        user.is_first_login = false;
        setCurrentUser(user);
      }
    });
  }
});
