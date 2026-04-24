// group-search 용 자바스크립트
(async () => {
requireLogin();
const posts = await apiGet('/neighbor/group-search');
const list = document.getElementById('group-search-list');

  if (posts.length === 0) {
    const p = document.createElement('p');
    p.className = 'meta-text';
    p.textContent = '등록된 모임이 없습니다.';
    list.appendChild(p);
    return;
  }


  posts.forEach(p => {
    const article = document.createElement('article');
    article.className = 'group-search-card';

    const title = document.createElement('strong');
    title.textContent = p.title;

    const authorEl = document.createElement('p');
    authorEl.className = 'meta-text';
    authorEl.style.marginTop = '0.25rem'
    authorEl.textContent = `${p.author?.nickname ?? '알 수 없음'} · 참여자 ${p.member_count}명`;

    const meta = document.createElement('p');
    meta.className = 'meta-text';
    meta.style.marginTop = '0.5rem';
    const categoryLabel = p.category ? ` · #${p.category}` : '';
    meta.textContent = `${p.group_type}${categoryLabel} · 함께할 습관: ${p.habit_title} · ${p.frequency}`;

    const createdEl = document.createElement('p');
    createdEl.className = 'meta-text';
    createdEl.style.marginTop = '0.25rem';
    createdEl.textContent = `등록 · ${new Date(p.created_at).toLocaleDateString('ko-KR')}`;
    
    let updatedEl = null;
    if (p.updated_at) {
      updatedEl = document.createElement('p');
      updatedEl.className = 'meta-text';
      updatedEl.style.marginTop = '0.25rem';
      updatedEl.textContent = `수정됨 · ${new Date(p.updated_at).toLocaleDateString('ko-KR')}`;
    }
    const desc = document.createElement('p');
    desc.style.marginTop = '0.5rem';
    desc.textContent = p.description ?? '';

    const actions = document.createElement('div');
    actions.className = 'page-actions';
    actions.style.marginTop = '1rem';

    const link = document.createElement('a');
    link.href = `/pages/neighbor/group-search-join.html?post_id=${p.post_id}&habit_title=${encodeURIComponent(p.habit_title)}&frequency=${encodeURIComponent(p.frequency)}`;
    link.className = 'btn btn-outline btn-sm';
    link.textContent = '함께하기';

    const currentUser = getCurrentUser(); // common.js의 함수
    if (currentUser && p.author?.id === currentUser.id) {
      const editLink = document.createElement('a');
      editLink.href = `/pages/neighbor/group-search-edit.html?post_id=${p.post_id}`;
      editLink.className = 'btn btn-outline btn-sm';
      editLink.textContent = '수정하기';
      actions.appendChild(editLink);
    }

    actions.appendChild(link);
    article.append(title, authorEl, meta, createdEl, ...(updatedEl ? [updatedEl] : []), desc, actions);
    list.appendChild(article);
  });
})();
