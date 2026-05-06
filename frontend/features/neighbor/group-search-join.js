// 수정: 버튼 클릭 시에만 API 호출
document.addEventListener('DOMContentLoaded', () => {
    const post_id = new URLSearchParams(location.search).get('post_id');
    const joinBtn = document.getElementById('join-confirm-btn');
    if (!joinBtn || !post_id) return;

    joinBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        try {
            const res = await fetch(`/api/v1/support/group/post/${post_id}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('gigi_token')}` }
            });

            if (res.status === 401) {
                alert('로그인이 필요합니다.');
                location.href = '/pages/auth/login.html';
                return;
            }
            const data = await res.json().catch(() => ({}));
            if (res.ok) {
                alert(data.message === "모임생성" ? '모임이 생성되었습니다.' : '모임 가입에 성공했습니다.');
                location.href = '/pages/support/index.html';
                return;
            }


            alert(data.detail || '모임 참가에 실패했습니다.');
        } catch {
            alert('네트워크 오류가 발생했습니다.');
        }
    });
});
