// 수정: 버튼 클릭 시에만 API 호출
// 함께하기로 참가할 때의 로직
document.addEventListener('DOMContentLoaded', () => {
    const post_id = new URLSearchParams(location.search).get('post_id');
    const joinBtn = document.getElementById('join-confirm-btn');
    if (!joinBtn || !post_id) return;

    joinBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        try {
            const data = await apiPost(`/support/group/post/${post_id}`);
            showToast(data.message === "모임생성" ? '모임이 생성되었습니다.' : '모임 가입에 성공했습니다.');
            location.href = '/pages/support/index.html';
        } catch (err) {
            showToast(err.message || '모임 참가에 실패했습니다.');
        }
    });
});
