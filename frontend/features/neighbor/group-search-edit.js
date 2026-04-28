(async () => {
  requireLogin();
  const postId = new URLSearchParams(location.search).get('post_id');
  if (!postId) { location.href = PAGES.groupSearch; return; }

  // 전체 목록에서 해당 글 찾아 폼에 채우기
  const posts = await apiGet('/neighbor/group-search');
  const post = posts.find(p => String(p.post_id) === postId);
  if (!post) { alert('글을 찾을 수 없습니다.'); location.href = PAGES.groupSearch; return; }

  document.getElementById('group_type').value = post.group_type;
  document.getElementById('title').value = post.title;
  document.getElementById('description').value = post.description;
  document.getElementById('habit_title').value = post.habit_title;
  // 변경 — 저장된 "월, 수, 금" 문자열을 파싱해서 해당 체크박스를 체크
  post.frequency.split(', ').forEach(day => {
    const cb = document.querySelector(`input[name="frequency"][value="${day}"]`);
    if (cb) cb.checked = true;
  });
  document.getElementById('category').value = post.category ?? '';
  document.getElementById('submit-btn').textContent = '수정 완료';

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
    try {
      await apiPut(`/neighbor/group-search/${postId}`, body);
      location.href = PAGES.myPosts;
    } catch (err) {
      alert(err.message || '수정에 실패했습니다.');
    }
  });
})();
