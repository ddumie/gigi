// feed-detail.js
// getCurrentUserId() 함수


const params = new URLSearchParams(location.search);
const postId = params.get('post_id');
if (!postId) { location.href = '/pages/neighbor/feed.html'; }

async function loadDetail() {
  try {
    const p = await apiGet(`/neighbor/feed/${postId}`);

    const el = document.getElementById('feed-detail-content');
    el.innerHTML = '';

    const nickname = p.author?.nickname ?? '알 수 없음';
    const firstChar = nickname.charAt(0);

    // 상단 행: 카테고리 뱃지
    const header = document.createElement('div');
    header.className = 'detail-header';

    const badge = document.createElement('span');
    badge.className = 'badge badge-blue';
    badge.textContent = p.category;

    header.append(badge);

    // 아바타 + 닉네임 행
    const memberRow = document.createElement('div');
    memberRow.className = 'member-row detail-member-row';

    const avatar = document.createElement('div');
    avatar.className = 'member-avatar';
    avatar.textContent = firstChar;

    const memberInfo = document.createElement('div');
    memberInfo.className = 'member-info';

    const memberName = document.createElement('div');
    memberName.className = 'member-name';
    memberName.textContent = nickname;

    memberInfo.appendChild(memberName);
    memberRow.append(avatar, memberInfo);


    // 본문
    const body = document.createElement('p');
    body.className = 'detail-body';
    body.textContent = p.content ?? '';

    el.append(header, memberRow, body);
    } catch (e) {
    console.error('피드 로드 실패', e);
    showToast('피드를 불러오는 중 오류가 발생했습니다.');
  }
}

async function loadComments() {
  try {
    const comments = await apiGet(`/neighbor/feed/${postId}/comments`);

    const list = document.getElementById('comment-list');
    list.innerHTML = '';

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
      card.className = 'feed-card';

      const commentNickname = c.author_nickname ?? '알 수 없음';
      const commentFirstChar = commentNickname.charAt(0);

      const memberRow = document.createElement('div');
      memberRow.className = 'member-row comment-member-row';

      const avatar = document.createElement('div');
      avatar.className = 'member-avatar';
      avatar.textContent = commentFirstChar;

      const memberInfo = document.createElement('div');
      memberInfo.className = 'member-info';

      const memberName = document.createElement('div');
      memberName.className = 'member-name';
      memberName.textContent = commentNickname;

      const createdAt = document.createElement('span');
      createdAt.className = 'meta-text';
      createdAt.textContent = c.created_at
        ? new Date(c.created_at).toLocaleDateString('ko-KR').replace(/\.$/, '')
        : '';

      memberInfo.append(memberName, createdAt);
      memberRow.append(avatar, memberInfo);

      const content = document.createElement('p');
      content.className = 'comment-content';
      content.textContent = c.content;

      card.append(memberRow, content);
        // 내 댓글일 때만 수정 버튼 표시
      if (c.author_id === currentUserId) {
        const editRow = document.createElement('div');
        editRow.className = 'comment-edit-row';

        const editBtn = document.createElement('button');
        editBtn.type = 'button';
        editBtn.className = 'btn btn-outline btn-sm';
        editBtn.textContent = '수정';
        // 삭제 버튼
        const deleteBtn = document.createElement('button');
        deleteBtn.type = 'button';
        deleteBtn.className = 'btn btn-outline btn-sm';
        deleteBtn.textContent = '삭제';
    // 댓글 삭제 버튼 구현
    deleteBtn.addEventListener('click', async () => {
    if (!confirm('댓글을 삭제하시겠습니까?')) return;
    try {
      await apiDelete(`/neighbor/feed/${postId}/comments/${c.id}`);
      await loadComments();
    } catch (e) {
      showToast('네트워크 오류가 발생했습니다.');
    }
    });

    // 수정 날짜 표시
    if (c.updated_at) {
      const editedAt = document.createElement('span');
      editedAt.className = 'meta-text';
      editedAt.textContent = `(수정됨 ${new Date(c.updated_at).toLocaleDateString('ko-KR')})`;
      editRow.append(editBtn, editedAt, deleteBtn);
    } else {
      editRow.append(editBtn, deleteBtn);
    }  

    editBtn.addEventListener('click', () => {
      document.getElementById('comment-input').value = c.content;
      document.getElementById('comment-input').focus();

      document.getElementById('comment-submit').classList.add('hidden');
      document.getElementById('comment-edit-submit').classList.remove('hidden');
      document.getElementById('comment-edit-cancel').classList.remove('hidden');

      // 이전에 등록된 이벤트 리스너를 교체하기 위해 복제
      const oldSave = document.getElementById('comment-edit-submit');
      const newSave = oldSave.cloneNode(true);
      oldSave.replaceWith(newSave);

      newSave.addEventListener('click', async () => {
        const newContent = document.getElementById('comment-input').value.trim();
        if (!newContent) return;
        try {
          await apiPut(`/neighbor/feed/${postId}/comments/${c.id}`,{ content: newContent });
          resetCommentInput();
          await loadComments();
        } catch {
          showToast('네트워크 오류가 발생했습니다.');
        }
      });
    });

    card.appendChild(editRow);  // editBtn 대신 editRow
  }


      list.appendChild(card);
    });
  } catch(e) {
    console.error('댓글 로드 실패', e);
    showToast('댓글을 불러오는 중 오류가 발생했습니다.');
  }
}
async function loadSupport() {
  try {
    const data = await apiGet(`/neighbor/feed/${postId}/support`);

    document.getElementById('support-count').textContent = data.support_count;
    const btn = document.getElementById('support-btn');
    btn.classList.toggle('btn-primary', data.is_supported);
    btn.classList.toggle('btn-outline', !data.is_supported);
  } catch (e) {
    console.error('지지 정보 로드 실패', e);
    showToast('지지 정보를 불러오는 중 오류가 발생했습니다.');
  }
}


function resetCommentInput() {
  document.getElementById('comment-input').value = '';
  document.getElementById('comment-submit').classList.remove('hidden');
  document.getElementById('comment-edit-submit').classList.add('hidden');
  document.getElementById('comment-edit-cancel').classList.add('hidden');
}
document.getElementById('comment-edit-cancel').addEventListener('click', () => {
  resetCommentInput();
});

document.getElementById('comment-submit').addEventListener('click', async () => {
  const content = document.getElementById('comment-input').value.trim();
  if (!content) return;
  try {
    await apiPost(`/neighbor/feed/${postId}/comments`, { content });
    document.getElementById('comment-input').value = '';
    await loadComments();
  } catch (e) {
    showToast('네트워크 오류가 발생했습니다.');
  }
});

// 이벤트 리스너들

document.getElementById('support-btn').addEventListener('click', async () => {
  try {
    await apiPost(`/neighbor/feed/${postId}/support`);
    await loadSupport();

  } catch (e) {
    showToast('네트워크 오류가 발생했습니다.');
  }
});


loadDetail();
loadComments();
loadSupport();