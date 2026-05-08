document.addEventListener('DOMContentLoaded', () => {
  requireLogin();
  const freqContainer = document.getElementById('freq-days');
  if (freqContainer) {
    freqContainer.outerHTML = dayPickerHtml('freq-days', '');
  }
});
