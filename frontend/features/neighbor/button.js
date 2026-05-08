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
try {
    const res = await apiPost('/neighbor/group-search', body);
    showToast('글이 등록되었습니다.')
    location.href = PAGES.myPosts;
} catch {
    showToast('네트워크 오류가 발생했습니다.');
}
});