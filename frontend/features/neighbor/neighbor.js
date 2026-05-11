document.addEventListener('DOMContentLoaded', () => {
  requireLogin();
  // freq-days 클래스의 체크박스 동적 형식으로 포메팅
  const freqContainer = document.getElementById('freq-days');
  if (freqContainer) {
    freqContainer.outerHTML = dayPickerHtml('freq-days', '');
  }
});
