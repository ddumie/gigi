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
  }
});

loadDetail();
loadComments();
