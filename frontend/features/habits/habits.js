document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-habit-filter]').forEach((chip) => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('[data-habit-filter]').forEach((item) => {
        item.classList.remove('active');
      });
      chip.classList.add('active');
    });
  });
});
