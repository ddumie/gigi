// feed-detail.js
const params = new URLSearchParams(location.search);
const postId = params.get('post_id');

async function loadDetail() {
  const res = await fetch(`/api/v1/neighbor/feed/${postId}`);
  if (!res.ok) return;
  const p = await res.json();

  const el = document.getElementById('feed-detail-content');
  el.innerHTML = '';

  const title = document.createElement('strong');
  title.textContent = `${p.category} 완료`;

  const author = document.createElement('p');
  author.className = 'meta-text';
  author.style.marginTop = '0.25rem';
  author.textContent = p.author?.nickname ?? '알 수 없음';

  const body = document.createElement('p');
  body.className = 'section-copy';
  body.style.marginTop = '0.5rem';
  body.textContent = p.content ?? '';

  el.append(title, author, body);
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

  comments.forEach(c => {
    const card = document.createElement('div');
    card.className = 'feed-card';

    const nick = document.createElement('strong');
    nick.textContent = c.author_nickname ?? '알 수 없음';

    const content = document.createElement('p');
    content.style.marginTop = '0.25rem';
    content.textContent = c.content;

    card.append(nick, content);
    list.appendChild(card);
  });
}
async function loadSupport() {
  const res = await fetch(`/api/v1/neighbor/feed/${postId}/support`);
  if (!res.ok) return;
  const data = await res.json();

  document.getElementById('support-count').textContent = data.support_count;
  const btn = document.getElementById('support-btn');
  btn.classList.toggle('btn-primary', data.is_supported);
  btn.classList.toggle('btn-outline', !data.is_supported);
}

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