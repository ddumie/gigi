document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.recommendation-card').forEach((card) => {
    card.addEventListener('click', () => {
      card.classList.toggle('active');
    });
  });
});
