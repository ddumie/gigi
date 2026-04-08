document.getElementById('submit-btn').addEventListener('click', async () => {
const body = {
    title: document.getElementById('title').value,
    description: document.getElementById('description').value,
    habit_title: document.getElementById('habit_title').value,
    frequency: document.getElementById('frequency').value,
};
const res = await fetch('/api/v1/neighbor/group-search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
});
if (res.ok) {
    location.href = '/pages/neighbor/group-search.html';
}
});