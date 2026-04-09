(async () => {
const res = await fetch('/api/v1/neighbor/group-search');
const posts = await res.json();
const list = document.getElementById('group-search-list');

if (posts.length === 0) {
    list.innerHTML = '<p class="meta-text">등록된 모임이 없습니다.</p>';
    return;
}

list.innerHTML = posts.map(p => `
    <article class="group-search-card">
    <strong>${p.title}</strong>
    <p class="meta-text" style="margin-top:0.5rem;">
        ${p.group_type} · 함께할 습관: ${p.habit_title} · ${p.frequency}
    </p>
    <p style="margin-top:0.5rem;">${p.description ?? ''}</p>
    <div class="page-actions" style="margin-top:1rem;">
        <a href="/pages/neighbor/group-search-join.html" class="btn btn-outline btn-sm">함께하기</a>
    </div>
    </article>
`).join('');
})();
