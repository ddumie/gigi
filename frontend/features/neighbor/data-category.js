// data-category.js

let allPosts = [];  // 전체 피드 캐시

// 피드 카드 렌더링
function renderFeed(posts) {
  const list = document.querySelector('.feed-list');
  list.innerHTML = '';

  if (posts.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'meta-text';
    empty.textContent = '등록된 피드가 없습니다.';
    list.appendChild(empty);
    return;
  }

  posts.forEach(p => {
    const article = document.createElement('article');
    article.className = 'feed-card';
    article.dataset.category = p.category;

    const title = document.createElement('strong');
    title.textContent = `${p.category} 완료`;

    const body = document.createElement('p');
    body.className = 'section-copy';
    body.style.marginTop = '0.5rem';
    body.textContent = p.content ?? '';

    const actions = document.createElement('div');
    actions.className = 'page-actions';
    actions.style.marginTop = '1rem';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-outline btn-sm support-toggle';
    btn.textContent = '지지하기';

    actions.appendChild(btn);
    const commentBtn = document.createElement('button');
    commentBtn.type = 'button';
    commentBtn.className = 'btn btn-outline btn-sm';
    commentBtn.textContent = '댓글';
    commentBtn.addEventListener('click', () => {
    location.href = `/pages/neighbor/feed-detail.html?post_id=${p.post_id}`;
    });
    
    actions.appendChild(commentBtn);
    article.append(title, body, actions);

    // 지지하기 토글
    btn.addEventListener('click', (e) => {
      const btn = e.currentTarget;
      btn.classList.toggle('active');
      btn.textContent = btn.classList.contains('active') ? '지지 취소' : '지지하기';
    });

    list.appendChild(article);
  });
}

// 카테고리 필터 칩 연결
function initCategoryFilter() {
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');

      const category = chip.dataset.category;
      const filtered = category === 'all'
        ? allPosts
        : allPosts.filter(p => p.category === category);

      renderFeed(filtered);
    });
  });
}

// 초기 로드
(async () => {
  const res = await fetch('/api/v1/neighbor/feed', { 
    headers: { 'Authorization': `Bearer ${localStorage.getItem('gigi_token')}` }
  });
  allPosts = await res.json();
  renderFeed(allPosts);
  initCategoryFilter();
})();
