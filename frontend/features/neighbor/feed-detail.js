// feed-detail.js
// getCurrentUserId() 함수
requireLogin()
function getCurrentUserId() {
  const token = localStorage.getItem('gigi_token');
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return parseInt(payload.sub, 10);
  } catch { return null; }
}


const params = new URLSearchParams(location.search);
const postId = params.get('post_id');

async function loadDetail() {
  const res = await fetch(`/api/v1/neighbor/feed/${postId}`, {
  headers: { 'Authorization': `Bearer ${localStorage.getItem('gigi_token')}` }
  });
  if (!res.ok) return;
  const p = await res.json();

  const el = document.getElementById('feed-detail-content');
  el.innerHTML = '';

  // 상단 행: 카테고리 뱃지 + 작성자
  const header = document.createElement('div');
  header.style.cssText = 'display:flex; align-items:center; gap:0.5rem; margin-bottom:0.75rem;';

  const badge = document.createElement('span');
  badge.className = 'badge badge-blue';
  badge.textContent = p.category;

  const author = document.createElement('span');
  author.className = 'meta-text';
  author.textContent = p.author?.nickname ?? '알 수 없음';

  header.append(badge, author);

  // 본문
  const body = document.createElement('p');
  body.style.cssText = 'font-size:1.05rem; line-height:1.7; margin:0;';
  body.textContent = p.content ?? '';

  el.append(header, body);
}

async function loadComments() {
  const res = await fetch(`/api/v1/neighbor/feed/${postId}/comments`);
  if (!res.ok) return;
  const comments = await res.json();

  const list = document.getElementById('comment-list');
  list.innerHTML = '';

  if (comments.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'meta-text';
    empty.textContent = '아직 댓글이 없습니다.';
    list.appendChild(empty);
    return;
  }

  const currentUserId = getCurrentUserId();
  comments.forEach(c => {
    const card = document.createElement('div');
    card.className = 'feed-card';

    const nick = document.createElement('strong');
    nick.textContent = c.author_nickname ?? '알 수 없음';

    const content = document.createElement('p');
    content.style.marginTop = '0.25rem';
    content.textContent = c.content;
    
    const createdAt = document.createElement('span');
    createdAt.className = 'meta-text';
    createdAt.textContent = c.created_at
      ? new Date(c.created_at).toLocaleDateString('ko-KR').replace(/\.$/, '')
      : '';

    card.append(nick, content, createdAt);
      // 내 댓글일 때만 수정 버튼 표시
if (c.author_id === currentUserId) {
  const editRow = document.createElement('div');
  editRow.style.cssText = 'display:flex; align-items:center; gap:0.5rem; margin-top:0.5rem;';

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
  const r = await fetch(`/api/v1/neighbor/feed/${postId}/comments/${c.id}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${localStorage.getItem('gigi_token')}` },
  });
  if (r.ok) {
    await loadComments();
  } else {
    alert('삭제에 실패했습니다.');
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

    document.getElementById('comment-submit').style.display = 'none';
    document.getElementById('comment-edit-submit').style.display = '';
    document.getElementById('comment-edit-cancel').style.display = '';

    // 이전에 등록된 이벤트 리스너를 교체하기 위해 복제
    const oldSave = document.getElementById('comment-edit-submit');
    const newSave = oldSave.cloneNode(true);
    oldSave.replaceWith(newSave);

    newSave.addEventListener('click', async () => {
      const newContent = document.getElementById('comment-input').value.trim();
      if (!newContent) return;
      const res = await fetch(`/api/v1/neighbor/feed/${postId}/comments/${c.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('gigi_token')}`,
        },
        body: JSON.stringify({ content: newContent }),
      });
      if (res.ok) {
        resetCommentInput();
        await loadComments();
      } else {
        alert('수정에 실패했습니다.');
      }
    });
  });

  card.appendChild(editRow);  // editBtn 대신 editRow
}


    list.appendChild(card);
  });
}
async function loadSupport() {
  const res = await fetch(`/api/v1/neighbor/feed/${postId}/support`, {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('gigi_token')}` }
  });
  if (!res.ok) return;
  const data = await res.json();

  document.getElementById('support-count').textContent = data.support_count;
  const btn = document.getElementById('support-btn');
  btn.classList.toggle('btn-primary', data.is_supported);
  btn.classList.toggle('btn-outline', !data.is_supported);
}
function resetCommentInput() {
  document.getElementById('comment-input').value = '';
  document.getElementById('comment-submit').style.display = '';
  document.getElementById('comment-edit-submit').style.display = 'none';
  document.getElementById('comment-edit-cancel').style.display = 'none';
}
document.getElementById('comment-edit-cancel').addEventListener('click', () => {
  resetCommentInput();
});

document.getElementById('comment-submit').addEventListener('click', async () => {
  const content = document.getElementById('comment-input').value.trim();
  if (!content) return;

  const res = await fetch(`/api/v1/neighbor/feed/${postId}/comments`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('gigi_token')}`,
    },
    body: JSON.stringify({ content }),
  });

  if (res.ok) {
    document.getElementById('comment-input').value = '';
    await loadComments();
  } else if (res.status === 401) {
    alert('로그인이 필요합니다.');
    location.href = '/pages/auth/login.html';
  } else {
    alert('댓글 등록에 실패했습니다. 다시 시도해주세요.');
  }
});

// 이벤트 리스너들

document.getElementById('support-btn').addEventListener('click', async () => {
  const res = await fetch(`/api/v1/neighbor/feed/${postId}/support`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${localStorage.getItem('gigi_token')}` }
  });
  if (res.ok) {
    await loadSupport();
  } else if (res.status === 401) {
    alert('로그인이 필요합니다.');
    location.href = '/pages/auth/login.html';
  }
});


loadDetail();
loadComments();
loadSupport();