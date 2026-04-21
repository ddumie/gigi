// 수정: 버튼 클릭 시에만 API 호출
document.addEventListener('DOMContentLoaded', () => {
    requireLogin();
    const post_id = new URLSearchParams(location.search).get('post_id');
    const joinBtn = document.getElementById('join-confirm-btn');
    if (!joinBtn || !post_id) return;

    joinBtn.addEventListener('click', async (e) => {
        e.preventDefault();

        const res = await fetch(`/api/v1/support/group/post/${post_id}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('gigi_token')}` }
        });

        if (res.status === 401) {
            alert('로그인이 필요합니다.');
            location.href = '/pages/auth/login.html';
            return;
        }

        if (res.ok) {
            location.href = '/pages/support/index.html';
            return;
        }

        const data = await res.json().catch(() => ({}));
        // 이미 가입된 경우(내가 만든 모임 포함)도 지지 페이지로 이동
        if ((data.detail ?? '').includes('이미 모임에 가입')) {
            location.href = '/pages/support/index.html';
            return;
        }

        alert(`오류: ${data.detail || '모임 참가에 실패했습니다.'}`);
    });
});
