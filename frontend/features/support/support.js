document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-support-button]').forEach((button) => {
    button.addEventListener('click', () => {
      button.disabled = true;
      button.textContent = '오늘 지지 완료';
      showToast('오늘의 지지를 보냈어요.');
    });
  });
});
