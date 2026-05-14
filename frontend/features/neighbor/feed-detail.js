// feed-detail.js
(() => {
  let currentEditCommentId = null;
  const params = new URLSearchParams(location.search);
  const postId = params.get('post_id');
  if (!postId) { location.href = '/pages/neighbor/feed.html'; return; }

  async function loadDetail() {
    try {
      const p = await apiGet(`/neighbor/feed/${postId}`);
      const el = document.getElementById('feed-detail-content');
      el.innerHTML = '';
      const card = document.getElementById('feed-detail-card');
      if (card) card.dataset.category = p.category ?? '기타';

      const nickname = p.author?.nickname ?? '알 수 없음';
      const firstChar = nickname.charAt(0);
      const timeAgo = formatRelativeTime(p.created_at);

      // ── 헤더: 아바타 + 닉네임 + 시간 / 카테고리 뱃지 ──
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

      // ── 습관 제목 박스 ──
      const titleBox = document.createElement('div');
      titleBox.className = 'feed-title-box';

      const titleIcon = document.createElement('span');
      titleIcon.className = 'feed-title-icon';
      titleIcon.textContent = '■';

      const categoryComplete = document.createElement('span');
      categoryComplete.className = 'feed-category-complete';
      categoryComplete.textContent = `[${p.category ?? '기타'} 완료]`;

      const titleText = document.createElement('span');
      titleText.textContent = p.habit_title ?? (p.group_name + ' 습관');

      titleBox.append(titleIcon, categoryComplete, titleText);

      // ── 모임/개인 뱃지 ──
      const groupLabel = document.createElement('div');
      groupLabel.className = 'group-label detail-group-label';
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

      // ── 본문 ──
      const body = document.createElement('p');
      body.className = 'section-copy';
      body.textContent = p.content ?? '';

      // ── 푸터: 지지 버튼 + 댓글 수 + 날짜 ──
      const actions = document.createElement('div');
      actions.className = 'feed-card-footer';

      const supportBtn = document.createElement('button');
      supportBtn.id = 'support-btn';
      supportBtn.type = 'button';
      supportBtn.className = 'btn btn-outline btn-sm feed-support-toggle';

      const commentCountBtn = document.createElement('button');
      commentCountBtn.type = 'button';
      commentCountBtn.className = 'btn btn-outline btn-sm';

      const dateStr = p.created_at
        ? new Date(p.created_at).toLocaleDateString('ko-KR', { year:'numeric', month:'2-digit', day:'2-digit' }).replace(/\.$/, '')
        : '';
      const dateEl = document.createElement('span');
      dateEl.className = 'meta-text feed-date';
      dateEl.textContent = dateStr;

      actions.append(supportBtn, commentCountBtn, dateEl);

      el.append(header, titleBox, groupLabel, body, actions);

      // 지지·댓글 수 초기 로드
      await loadSupport(supportBtn, p.support_count ?? 0, p.is_supported ?? false);
      updateCommentCountBtn(commentCountBtn, p.comment_count ?? 0);
    } catch (e) {
      console.error('피드 로드 실패', e);
      showToast('피드를 불러오는 중 오류가 발생했습니다.');
    }
  }

  async function loadSupport(btn, initialCount, initialSupported) {
    if (!btn) return;
    try {
      const data = await apiGet(`/neighbor/feed/${postId}/support`);
      renderSupportBtn(btn, data.support_count, data.is_supported);
    } catch {
      renderSupportBtn(btn, initialCount, initialSupported);
    }

    btn.addEventListener('click', async () => {
      try {
        const data = await apiPost(`/neighbor/feed/${postId}/support`);
        renderSupportBtn(btn, data.support_count, data.is_supported);
      } catch {
        showToast('네트워크 오류가 발생했습니다.');
      }
    });
  }

  function renderSupportBtn(btn, count, isSupported) {
    btn.textContent = `🔥 지지 ${count}`;
    isSupported
      ? btn.classList.replace('btn-outline', 'btn-primary')
      : btn.classList.replace('btn-primary', 'btn-outline');
  }

  function updateCommentCountBtn(btn, count) {
    if (!btn) return;
    btn.textContent = `💬 댓글 ${count}`;
    btn.style.cursor = 'default';
    btn.style.pointerEvents = 'none';
  }

  async function loadComments() {
    try {
      const comments = await apiGet(`/neighbor/feed/${postId}/comments`);
      const list = document.getElementById('comment-list');
      list.innerHTML = '';

      // 댓글 수 버튼 동기화
      const countBtn = document.querySelector('.feed-card-footer .btn-outline:last-of-type');
      if (countBtn && countBtn.textContent.startsWith('💬')) {
        updateCommentCountBtn(countBtn, comments.length);
      }

      if (comments.length === 0) {
        const empty = document.createElement('p');
        empty.className = 'meta-text';
        empty.textContent = '아직 댓글이 없습니다.';
        list.appendChild(empty);
        return;
      }

      const currentUserId = getCurrentUser()?.id ?? null;
      comments.forEach(c => {
        const card = document.createElement('div');
        card.className = 'comment-item';

        const commentNickname = c.author_nickname ?? '알 수 없음';
        const memberRow = document.createElement('div');
        memberRow.className = 'member-row comment-member-row';

        const avatar = document.createElement('div');
        avatar.className = 'member-avatar comment-avatar';
        avatar.textContent = commentNickname.charAt(0);

        const memberInfo = document.createElement('div');
        memberInfo.className = 'member-info';

        const memberName = document.createElement('div');
        memberName.className = 'member-name';
        memberName.textContent = commentNickname;

        const createdAt = document.createElement('span');
        createdAt.className = 'meta-text';
        createdAt.textContent = c.created_at
          ? (() => {
              const d = new Date(c.created_at);
              const date = d.toLocaleDateString('ko-KR').replace(/\.$/, '');
              const time = d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: false });
              return `${date} ${time}`;
            })()
          : '';

        memberInfo.append(memberName, createdAt);
        memberRow.append(avatar, memberInfo);

        const content = document.createElement('p');
        content.className = 'comment-content';
        content.textContent = c.content;

        card.append(memberRow, content);

        if (c.author_id === currentUserId) {
          const editRow = document.createElement('div');
          editRow.className = 'comment-edit-row';

          const editBtn = document.createElement('button');
          editBtn.type = 'button';
          editBtn.className = 'btn btn-outline btn-sm comment-action-btn';
          editBtn.textContent = '수정';

          const deleteBtn = document.createElement('button');
          deleteBtn.type = 'button';
          deleteBtn.className = 'btn btn-outline btn-sm comment-action-btn';
          deleteBtn.textContent = '삭제';

          deleteBtn.addEventListener('click', async () => {
            if (!confirm('댓글을 삭제하시겠습니까?')) return;
            try {
              await apiDelete(`/neighbor/feed/${postId}/comments/${c.id}`);
              await loadComments();
            } catch {
              showToast('네트워크 오류가 발생했습니다.');
            }
          });

          if (c.updated_at) {
            const editedAt = document.createElement('span');
            editedAt.className = 'meta-text';
            editedAt.textContent = `(수정됨 ${new Date(c.updated_at).toLocaleDateString('ko-KR')})`;
            editRow.append(editBtn, editedAt, deleteBtn);
          } else {
            editRow.append(editBtn, deleteBtn);
          }

          editBtn.addEventListener('click', () => {
            currentEditCommentId = c.id;
            document.getElementById('comment-input').value = c.content;
            document.getElementById('comment-input').focus();
            document.getElementById('comment-submit').classList.add('hidden');
            document.getElementById('comment-edit-submit').classList.remove('hidden');
            document.getElementById('comment-edit-cancel').classList.remove('hidden');
          });

          card.appendChild(editRow);
        }

        list.appendChild(card);
      });
    } catch (e) {
      console.error('댓글 로드 실패', e);
      showToast('댓글을 불러오는 중 오류가 발생했습니다.');
    }
  }

  function resetCommentInput() {
    document.getElementById('comment-input').value = '';
    document.getElementById('comment-submit').classList.remove('hidden');
    document.getElementById('comment-edit-submit').classList.add('hidden');
    document.getElementById('comment-edit-cancel').classList.add('hidden');
  }

  document.getElementById('comment-edit-cancel').addEventListener('click', resetCommentInput);

  document.getElementById('comment-edit-submit').addEventListener('click', async () => {
    if (!currentEditCommentId) return;
    const newContent = document.getElementById('comment-input').value.trim();
    if (!newContent) return;
    try {
      await apiPut(`/neighbor/feed/${postId}/comments/${currentEditCommentId}`, { content: newContent });
      currentEditCommentId = null;
      resetCommentInput();
      await loadComments();
    } catch {
      showToast('네트워크 오류가 발생했습니다.');
    }
  });

  document.getElementById('comment-submit').addEventListener('click', async () => {
    const content = document.getElementById('comment-input').value.trim();
    if (!content) return;
    try {
      await apiPost(`/neighbor/feed/${postId}/comments`, { content });
      document.getElementById('comment-input').value = '';
      await loadComments();
    } catch {
      showToast('네트워크 오류가 발생했습니다.');
    }
  });

  loadDetail().then(() => loadComments());
})();
