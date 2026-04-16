document.addEventListener('DOMContentLoaded', () => {
  requireLogin();
  document.querySelectorAll('.support-toggle').forEach((button) => {
    button.addEventListener('click', () => {
      button.classList.toggle('active');
      button.textContent = button.classList.contains('active') ? '지지 취소' : '지지하기';
    });
  });
});
