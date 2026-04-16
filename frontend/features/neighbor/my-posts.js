// my-posts 용 자바스크립트
(async () => {
  requireLogin();
  const [groupRes, feedRes] = await Promise.all([
    fetch('/api/v1/neighbor/group-search/my'),
    fetch('/api/v1/neighbor/feed/my')
  ]);

  const groupPosts = await groupRes.json();
  const feedPosts = await feedRes.json();
  // group-search 글 렌더링
  const list_gs = document.getElementById('my-posts-list-gs');
  groupPosts.forEach(p => {
    const article = document.createElement('article');
    article.className = 'group-search-card';

    const title = document.createElement('strong');
    title.textContent = p.title;

    const meta = document.createElement('p');
    meta.className = 'meta-text';
    meta.textContent = `모임 구해요 · ${p.group_type} · ${p.habit_title}`;

    article.append(title, meta);
    list_gs.appendChild(article);
  });

  // feed 글 렌더링
  const list_f = document.getElementById('my-posts-list-fd')
  feedPosts.forEach(p => {
    const article = document.createElement('article');
    article.className = 'feed-card';

    const title = document.createElement('strong');
    title.textContent = `${p.category} 완료`;

    const body = document.createElement('p');
    body.textContent = p.content ?? '';

    article.append(title, body);
    list_f.appendChild(article);
  });
})();


