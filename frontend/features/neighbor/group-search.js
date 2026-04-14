// group-search 용 자바스크립트
(async () => {
const res = await fetch('/api/v1/neighbor/group-search');
const posts = await res.json();
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

    const meta = document.createElement('p');
    meta.className = 'meta-text';
    meta.style.marginTop = '0.5rem';
    meta.textContent = `${p.group_type} · 함께할 습관: ${p.habit_title} · ${p.frequency}`;

    const desc = document.createElement('p');
    desc.style.marginTop = '0.5rem';
    desc.textContent = p.description ?? '';

    const actions = document.createElement('div');
    actions.className = 'page-actions';
    actions.style.marginTop = '1rem';

    const link = document.createElement('a');
    link.href = `/pages/neighbor/group-search-join.html?habit_title=${encodeURIComponent(p.habit_title)}&frequency=${encodeURIComponent(p.frequency)}`;
    link.className = 'btn btn-outline btn-sm';
    link.textContent = '함께하기';

    actions.appendChild(link);
    article.append(title, meta, desc, actions);
    list.appendChild(article);
  });
})();
