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

    const nickname = p.author?.nickname ?? '알 수 없음';
    const firstChar = nickname.charAt(0);
    const dateStr = p.created_at
      ? new Date(p.created_at).toLocaleDateString('ko-KR', { year:'numeric', month:'2-digit', day:'2-digit' }).replace(/\.$/, '')
      : '';

    // 헤더: 아바타 + 닉네임 + 등록날짜
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

    const memberDate = document.createElement('div');
    memberDate.className = 'meta-text';
    memberDate.textContent = dateStr;

    memberInfo.append(memberName, memberDate);
    memberRow.append(avatar, memberInfo);
    header.append(memberRow);

    // 제목 박스 (■ 아이콘 + 제목)
    const titleBox = document.createElement('div');
    titleBox.className = 'feed-title-box';

    const titleIcon = document.createElement('span');
    titleIcon.className = 'feed-title-icon';
    titleIcon.textContent = '■';

    const titleText = document.createElement('span');
    titleText.textContent = p.title;

    titleBox.append(titleIcon, titleText);

    // 세부 정보 (모임유형, 카테고리, 습관, 빈도)
    const meta = document.createElement('p');
    meta.className = 'meta-text';
    meta.style.marginTop = '0.5rem';
    const categoryLabel = p.category ? ` · #${p.category}` : '';
    meta.textContent = `${p.group_type}${categoryLabel} · 함께할 습관: ${p.habit_title} · ${p.frequency}`;

    // 글 세부내용 (description)
    const desc = document.createElement('p');
    desc.className = 'section-copy';
    desc.textContent = p.description ?? '';

    // 하단: 참여자 수 + 버튼
    const footer = document.createElement('div');
    footer.className = 'feed-card-footer';

    const memberCount = document.createElement('span');
    memberCount.className = 'meta-text';
    memberCount.textContent = `참여자 ${p.member_count}명`;

    const btnGroup = document.createElement('div');
    btnGroup.style.cssText = 'margin-left:auto; display:flex; gap:0.5rem;';

    const link = document.createElement('a');
    link.href = `/pages/neighbor/group-search-join.html?post_id=${p.post_id}&habit_title=${encodeURIComponent(p.habit_title)}&frequency=${encodeURIComponent(p.frequency)}`;
    link.className = 'btn btn-outline btn-sm';
    link.textContent = '함께하기';

    btnGroup.appendChild(link);
    footer.append(memberCount, btnGroup);

    article.append(header, titleBox, meta, desc, footer);
    list.appendChild(article);
  });

})();
