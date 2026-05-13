// data-category.js
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
  let lastDate = null;
  for (const p of posts) {
    const article = document.createElement('article');
    article.className = 'feed-card';
    article.dataset.category = p.category;

    //날짜 구분선
    const postDate = p.created_at
      ? new Date(p.created_at).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })
      : '';
    if (postDate && postDate !== lastDate) {
      const sep = document.createElement('div');
      sep.className = 'feed-date-separator';
      sep.textContent = postDate;
      list.appendChild(sep);
      lastDate = postDate;
    }
    // 1. 상단: 아바타 + 닉네임 + 시간 / 카테고리 뱃지
    // 습관 피드 글쓴이 닉네임만 공개
    const nickname = p.author?.nickname ?? '알 수 없음';
    const firstChar = nickname.charAt(0);
    const timeAgo = formatRelativeTime(p.created_at);

    const header = document.createElement('div');
    header.className = 'feed-card-header';

    const memberRow = document.createElement('div');
    memberRow.className = 'member-row detail-row';

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

    // 2. 습관 제목 (음영 박스)
    const titleBox = document.createElement('div');
    titleBox.className = 'feed-title-box';

    // titleBox 아래에 개인/모임 뱃지
    const groupLabel = document.createElement('div');
    groupLabel.className = 'group-label detail-group-label';

    // 개인습관, group에 포함된 습관 여부 확인 후 표시
    const groupBadge = document.createElement('span');
    if (p.group_id && p.group_name && p.is_member) {
      groupBadge.className = 'badge badge-green';
      groupBadge.textContent = p.group_name;
    } else if (p.group_id && !p.group_name) {
      groupBadge.className = 'badge badge-gray';
      groupBadge.textContent = '없어진 모임입니다.';
    } else if (p.group_id && p.group_name && !p.is_member) {
      groupBadge.className = 'badge badge-gray';
      groupBadge.textContent = `탈퇴한 모임 · ${p.group_name}`;
    } else {
      groupBadge.className = 'badge badge-gray';
      groupBadge.textContent = '개인 습관';
    }
    groupLabel.appendChild(groupBadge);

    // 네모 아이콘
    const titleIcon = document.createElement('span');
    titleIcon.className = 'feed-title-icon';
    titleIcon.textContent = '■';

    // 습관 명 완료, 습관 타이틀 표시
    const categoryComplete = document.createElement('span');
    categoryComplete.className = 'feed-category-complete';
    categoryComplete.textContent = `[${p.category ?? '기타'} 완료]`;

    const titleText = document.createElement('span');
    titleText.textContent = p.habit_title ?? (p.group_name + ' 습관');

    titleBox.append(titleIcon, categoryComplete, titleText);

    // 지지버튼, 댓글 수
    const body = document.createElement('p');
    body.className = 'section-copy';
    body.textContent = p.content ?? '';
    // 하단: 지지 버튼 + 날짜
    const actions = document.createElement('div');
    actions.className = 'feed-card-footer';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-outline btn-sm feed-support-toggle';

    const dateStr = p.created_at ? new Date(p.created_at).toLocaleDateString('ko-KR', { year:'numeric', month:'2-digit', day:'2-digit' }).replace(/\.$/,'') : '';
    // 초기 지지 상태 로드
    let is_supported = p.is_supported ?? false;
    btn.textContent = `🔥 지지 ${p.support_count ?? 0}`;
    if (p.is_supported) btn.classList.replace('btn-outline', 'btn-primary');

    btn.addEventListener('click', async () => {
      try {
        const data = await apiPost(`/neighbor/feed/${p.post_id}/support`);
        is_supported = data.is_supported;
        btn.textContent = `🔥 지지 ${data.support_count}`;
        is_supported ? btn.classList.replace('btn-outline', 'btn-primary') : btn.classList.replace('btn-primary', 'btn-outline');
      } catch {
        showToast('네트워크 오류가 발생했습니다.');
      }
    });

    // 댓글수와 오늘 단 댓글 있는 경우 여부 표시
    const commentBtn = document.createElement('button');
    commentBtn.type = 'button';
    commentBtn.className = 'btn btn-outline btn-sm';
    commentBtn.textContent = `💬 댓글 ${p.comment_count ?? 0}`;

    if (p.has_my_comment_today) {
      commentBtn.classList.replace('btn-outline', 'btn-primary');
    }

    commentBtn.addEventListener('click', () => {
      location.href = `/pages/neighbor/feed-detail.html?post_id=${p.post_id}`;
    });

    const dateEl = document.createElement('span');
    dateEl.className = 'meta-text feed-date';
    dateEl.textContent = dateStr;
    // 포스팅
    actions.append(btn, commentBtn, dateEl);
    article.append(header, titleBox, groupLabel, body, actions);
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
      let filtered;
      if (category === 'all') {
        filtered = allPosts;
      } else if (category === 'my') {
        const me = getCurrentUser();
        filtered = me ? allPosts.filter(p => p.author?.id === me.id) : [];
      } else {
        filtered = allPosts.filter(p => p.category === category);
      }

      renderFeed(filtered);
    });
  });
}

// 초기 로드
(async () => {
  try {
    allPosts = await apiGet('/neighbor/feed');
    renderFeed(allPosts);
    initCategoryFilter();
  } catch {
    showToast('피드를 불러오는 중 오류가 발생했습니다.');
  }
})();
