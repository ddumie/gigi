document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.js-logout').forEach((button) => {
    button.addEventListener('click', logout);
  });
});
