// data-category.js
function formatTimeAgo(date) {
  const diff = Math.floor((Date.now() - date) / 1000 / 60);
  if (diff < 1) return '방금 전';
  if (diff < 60) return `${diff}분 전`;
  if (diff < 1440) return `${Math.floor(diff / 60)}시간 전`;
  return `${Math.floor(diff / 1440)}일 전`;
}

let allPosts = [];  // 전체 피드 캐시

// 피드 카드 렌더링
async function renderFeed(posts) {
  const list = document.querySelector('.feed-list');
  list.innerHTML = '';

  if (posts.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'meta-text';
    empty.textContent = '등록된 피드가 없습니다.';
    list.appendChild(empty);
    return;
  }

  for (const p of posts) {
    const article = document.createElement('article');
    article.className = 'feed-card';
    article.dataset.category = p.category;

    const nickname = p.author?.nickname ?? '알 수 없음';
    const firstChar = nickname.charAt(0);
    const timeAgo = p.created_at ? formatTimeAgo(new Date(p.created_at)) : '';

      // 1. 상단: 아바타 + 닉네임 + 시간 / 카테고리 뱃지
    const header = document.createElement('div');
    header.className = 'feed-card-header';

    const memberRow = document.createElement('div');
    memberRow.className = 'member-row';
    memberRow.style.cssText = 'padding:0; background:none;';

    const avatar = document.createElement('div');
    avatar.className = 'member-avatar';
    avatar.textContent = firstChar;

    const memberInfo = document.createElement('div');
    memberInfo.className = 'member-info';

    const memberName = document.createElement('div');
    memberName.className = 'member-name';
    memberName.textContent = nickname;

    const memberTime = document.createElement('div');
    memberTime.className = 'meta-text';
    memberTime.textContent = timeAgo;

    memberInfo.append(memberName, memberTime);
    memberRow.append(avatar, memberInfo);

    const categoryBadge = document.createElement('span');
    categoryBadge.className = 'feed-category-badge';
    categoryBadge.textContent = p.category ?? '기타';

    header.append(memberRow, categoryBadge);
    // 습관 피드 글쓴이 닉네임만 공개
    // 2. 습관 제목 (음영 박스)
    const titleBox = document.createElement('div');
    titleBox.className = 'feed-title-box';

    const titleIcon = document.createElement('span');
    titleIcon.className = 'feed-title-icon';
    titleIcon.textContent = '■';

    const titleText = document.createElement('span');
    titleText.textContent = p.habit_title ?? (p.category + ' 완료');

    titleBox.append(titleIcon, titleText);

    // 3. 본문
    const body = document.createElement('p');
    body.className = 'section-copy';
    body.textContent = p.content ?? '';
    // 하단: 지지 버튼 + 날짜
    const actions = document.createElement('div');
    actions.className = 'feed-card-footer';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-outline btn-sm feed-support-toggle';

    const dateStr = p.created_at ? new Date(p.created_at).toLocaleDateString('ko-KR', { year:'numeric', month:'2-digit', day:'2-digit' }).replace(/\. /g,'.').replace('.','') : '';
    // 초기 지지 상태 로드
    const res = await fetch(`/api/v1/neighbor/feed/${p.post_id}/support`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('gigi_token')}` }
    })
    const data = res.ok ? await res.json() : null;
    if (!data) continue;
    let is_supported = data.is_supported;
    btn.textContent = `🔥 지지 ${data.support_count}`;
    if (data.is_supported) btn.classList.replace('btn-outline', 'btn-primary');
   
  btn.addEventListener('click', async () => {
    const r = await fetch(`/api/v1/neighbor/feed/${p.post_id}/support`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('gigi_token')}` }
    });
    if (r.status === 401) { alert('로그인이 필요합니다.'); location.href = '/pages/auth/login.html'; return; }
    if (!r.ok) return;
    const current = parseInt(btn.textContent.replace(/[^0-9]/g, '')) || 0;
    is_supported = !is_supported;
    btn.textContent = `🔥 지지 ${is_supported ? current + 1 : current - 1}`;
    is_supported ? btn.classList.replace('btn-outline', 'btn-primary') : btn.classList.replace('btn-primary', 'btn-outline');
  });

    // =================================================================================

    
    const commentBtn = document.createElement('button');
    commentBtn.type = 'button';
    commentBtn.className = 'btn btn-outline btn-sm';
    commentBtn.textContent = '댓글';
    commentBtn.addEventListener('click', () => {
    location.href = `/pages/neighbor/feed-detail.html?post_id=${p.post_id}`;
    });

    const dateEl = document.createElement('span');
    dateEl.className = 'meta-text feed-date';
    dateEl.textContent = dateStr;

    actions.append(btn, commentBtn, dateEl);
    article.append(header, titleBox, body, actions);
    list.appendChild(article);
  }
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
  if (!res.ok) return;
  allPosts = await res.json();
  renderFeed(allPosts);
  initCategoryFilter();
})();
