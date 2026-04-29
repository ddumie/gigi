// 글쓴 후 글 등록하기 버튼처리
document.getElementById('group-search-form').addEventListener('submit', async (e) => {
    e.preventDefault();
const body = {
    group_type: document.getElementById('group_type').value,
    title: document.getElementById('title').value,
    description: document.getElementById('description').value,
    habit_title: document.getElementById('habit_title').value,
    frequency: Array.from(document.querySelectorAll('input[name="frequency"]:checked')).map(cb => cb.value).join(', '),
    category: document.getElementById('category').value || null,
};
// current_user.id로 교체
const res = await fetch('/api/v1/neighbor/group-search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
     },
    body: JSON.stringify(body),
});
if (res.ok) {
    location.href = '/pages/neighbor/group-search.html';
} else if (res.status === 401) {
    alert('로그인이 필요합니다.');
    location.href = '/pages/auth/login.html';
} else if (res.status === 422) {
    alert('입력값을 다시 확인해주세요.');
} else {
    alert('글 등록에 실패했습니다. 다시 시도해주세요.');
}
});