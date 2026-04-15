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
    btn.textContent = '지지하기 ❤ 0';

    // 초기 지지 상태 로드
    fetch(`/api/v1/neighbor/feed/${p.post_id}/support`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('gigi_token')}` }
    }).then(res => res.ok ? res.json() : null).then(data => {
      if (!data) return;
      btn.textContent = `지지하기 ❤ ${data.support_count}`;
      if (data.is_supported) btn.classList.replace('btn-outline', 'btn-primary');
    });

    // =================================================================================

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
  // 클릭 시 API 호출
  btn.addEventListener('click', async () => {
    const res = await fetch(`/api/v1/neighbor/feed/${p.post_id}/support`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('gigi_token')}` }
    });
    if (res.status === 401) {
      alert('로그인이 필요합니다.');
      location.href = '/pages/auth/login.html';
      return;
    }
    if (!res.ok) return;

    const info = await fetch(`/api/v1/neighbor/feed/${p.post_id}/support`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('gigi_token')}` }
    }).then(r => r.json());

    btn.textContent = `지지하기 ❤ ${info.support_count}`;
    if (info.is_supported) {
      btn.classList.replace('btn-outline', 'btn-primary');
    } else {
      btn.classList.replace('btn-primary', 'btn-outline');
    }
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
