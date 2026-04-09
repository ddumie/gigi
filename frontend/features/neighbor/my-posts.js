// my-posts 용 자바스크립트
(async () => {
const res = await fetch('/api/v1/neighbor/group-search/my');
const posts = await res.json();
const list = document.getElementById('my-posts-list');

if (posts.length === 0) {
    list.innerHTML = '<p class="meta-text">작성한 글이 없습니다.</p>';
    return;
}

list.innerHTML = posts.map(p => `
    <article class="group-search-card">
    <strong>${p.title}</strong>
    <p class="meta-text" style="margin-top:0.5rem;">
        ${p.group_type} · 함께할 습관: ${p.habit_title} · ${p.frequency}
    </p>
    <p style="margin-top:0.5rem;">${p.description ?? ''}</p>
    </article>
`).join('');
})();

