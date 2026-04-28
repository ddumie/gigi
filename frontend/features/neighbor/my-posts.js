// my-posts 용 자바스크립트
(async () => {
  requireLogin();
  const [groupPosts, feedPosts] = await Promise.all([
    apiGet('/neighbor/group-search/my'),
    apiGet('/neighbor/feed/my')
  ]);

  // group-search 글 렌더링
  const list_gs = document.getElementById('my-posts-list-gs');
  let lastDateGs = null;
  groupPosts.forEach(p => {
    const article = document.createElement('article');
    article.className = 'group-search-card';

    // 아래 블록 추가
    const postDate = p.created_at
      ? new Date(p.created_at).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })
      : '';
    if (postDate && postDate !== lastDateGs) {
      const sep = document.createElement('div');
      sep.className = 'feed-date-separator';
      sep.textContent = postDate;
      list_gs.appendChild(sep);
      lastDateGs = postDate;
    }
    // 여기까지 추가
    const title = document.createElement('strong');
    title.textContent = p.title;

    const meta = document.createElement('p');
    meta.className = 'meta-text';
    meta.textContent = `모임 구해요 · ${p.group_type} · ${p.habit_title}`;

    const editLink = document.createElement('a');
    editLink.href = `/pages/neighbor/group-search-edit.html?post_id=${p.post_id}`;
    editLink.className = 'btn btn-outline btn-sm';
    editLink.style.marginTop = '0.75rem';
    editLink.textContent = '수정하기';

    article.append(title, meta, editLink);
    list_gs.appendChild(article);
  });

  // feed 글 렌더링
  const list_f = document.getElementById('my-posts-list-fd')
  let lastDateFd = null;
  feedPosts.forEach(p => {
    const article = document.createElement('article');
    article.className = 'feed-card';

    // 아래 블록 추가
    const postDate = p.created_at
      ? new Date(p.created_at).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })
      : '';
    if (postDate && postDate !== lastDateFd) {
      const sep = document.createElement('div');
      sep.className = 'feed-date-separator';
      sep.textContent = postDate;
      list_f.appendChild(sep);
      lastDateFd = postDate;
    }
    // 여기까지 추가
    
    const title = document.createElement('strong');
    title.textContent = `${p.category} 완료`;

    const body = document.createElement('p');
    body.textContent = p.content ?? '';

    article.append(title, body);
    list_f.appendChild(article);
  });
})();


