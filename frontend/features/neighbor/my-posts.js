// my-posts 용 자바스크립트
(async () => {
  let groupPosts, feedResult;
  try {
    [groupPosts, feedResult] = await Promise.all([
      apiGet('/neighbor/group-search/my'),
      apiGet('/neighbor/feed/my')
    ]);
  } catch {
    showToast('데이터를 불러오는 중 오류가 발생했습니다.');
    return;
  }
  // 모임, 습관피드 긱긱 병렬적으로 포스팅
  if (!groupPosts || !feedResult) {
    showToast('데이터를 불러올 수 없습니다.');
    return;
  }
  // 오늘 습관 완료 여부 전달
  const feedPosts = feedResult.posts ?? [];
  const allHabitsDone = feedResult.today_all_done;
  const todayStr = new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });

  // group-search 글 렌더링
  const list_gs = document.getElementById('my-posts-list-gs');
  let lastDateGs = null;
  groupPosts.forEach(p => {
    const article = document.createElement('article');
    article.className = 'group-search-card';
    article.hidden = true;

    // 날짜 버튼에 오늘 모임 목록 조회.
    // arrow로 보였다 숨기기 할 수 있음.
    const postDate = p.created_at
      ? new Date(p.created_at).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })
      : '';
    if (postDate && postDate !== lastDateGs) {
      const sep = document.createElement('div');
      sep.className = 'feed-date-separator detail-feed-date-separator';
      sep.textContent = postDate;
      const arrow = document.createElement('span');
      arrow.textContent = ' ▶';
      sep.appendChild(arrow);
      sep.addEventListener('click', () => {
        let el = sep.nextElementSibling;
        let collapsed = false;
        while (el && !el.classList.contains('feed-date-separator')) {
          el.hidden = !el.hidden;
          collapsed = el.hidden;
          el = el.nextElementSibling;
        }
        arrow.textContent = collapsed ? ' ▶' : ' ▼';
      });
      list_gs.appendChild(sep);
      lastDateGs = postDate;
    }
    // 본문
    const title = document.createElement('strong');
    title.textContent = p.title;

    const meta = document.createElement('p');
    meta.className = 'meta-text';
    meta.textContent = `모임 구해요 · ${p.group_type} · ${p.habit_title} · 참가자 ${p.member_count}명`;

    const editLink = document.createElement('a');
    editLink.href = `/pages/neighbor/group-search-edit.html?post_id=${p.post_id}`;
    editLink.className = 'btn btn-outline btn-sm edit-link';
    editLink.textContent = '수정하기';

    article.append(title, meta, editLink);
    list_gs.appendChild(article);
  });

  // feed 글 렌더링
  const list_f = document.getElementById('my-posts-list-fd');
  let lastDateFd = null;
  feedPosts.forEach(p => {
    // 날짜버튼에 오늘 완료한 습관피드 조회
    // arrow로 보였다 숨기기 할 수 있음
    const postDate = p.created_at
      ? new Date(p.created_at).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })
      : '';

    const article = document.createElement('article');
    article.className = 'feed-card';
    article.hidden = postDate !== todayStr;

    if (postDate && postDate !== lastDateFd) {
      const sep = document.createElement('div');
      sep.className = 'feed-date-separator';
      const dateSpan = document.createElement('span');
      dateSpan.textContent = postDate;
      sep.appendChild(dateSpan);
      // 기본적으로 오늘 한 습관피드는 디폴트로 보여지게 함.
      const arrow = document.createElement('span');
      arrow.className = 'date-arrow';
      arrow.textContent = postDate === todayStr ? ' ▼' : ' ▶';
      sep.appendChild(arrow);

      // 오늘 습관 모두 완료했으면 '모두 완료' 뜨도록 함
      if (postDate === todayStr && allHabitsDone) {
        const badge = document.createElement('span');
        badge.className = 'all-done-badge';
        badge.textContent = '모두 완료';
        sep.appendChild(badge);
      }
      sep.className = 'feed-date-separator detail-feed-date-separator';
      sep.addEventListener('click', () => {
        let el = sep.nextElementSibling;
        let collapsed = false;
        while (el && !el.classList.contains('feed-date-separator')) {
          el.hidden = !el.hidden;
          collapsed = el.hidden;
          el = el.nextElementSibling;
        }
        const arrow = sep.querySelector('.date-arrow');
        if (arrow) arrow.textContent = collapsed ? ' ▶' : ' ▼';
      });
      list_f.appendChild(sep);
      lastDateFd = postDate;
    }
    // 본문

    const title = document.createElement('strong');
    title.textContent = `${p.category} 완료 · ${p.habit_title ?? (p.group_name ? p.group_name + ' 습관' : '')}`;

    const body = document.createElement('p');
    body.textContent = p.content ?? '';

    article.append(title, body);
    list_f.appendChild(article);
  });
})();
