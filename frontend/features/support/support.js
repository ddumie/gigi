// document.addEventListener('DOMContentLoaded', () => {
//   document.querySelectorAll('[data-support-button]').forEach((button) => {
//     button.addEventListener('click', () => {
//       button.disabled = true;
//       button.textContent = '오늘 지지 완료';
//       showToast('오늘의 지지를 보냈어요.');
//     });
//   });
// });


// =============그룹 리스트 출력===============
const groupList = document.querySelector(".group-list");
let groupOffset = 0;
const groupLimit = 3;
let loading = false;

async function sendSupport(groupId, toUserId, button, card) {
  try {
    const res = await fetch(`/api/v1/support/group/${groupId}/support/${toUserId}`, {
      method: "POST"
    });
    if (!res.ok) {
      const err = await res.json();
      showToast(err.detail || "지지 실패");
      return;
    }
    await res.json(); // SupportResponse는 여기서 사용하지 않음

    // 버튼 상태 변경
    button.disabled = true;
    button.textContent = "오늘 지지 완료";
    showToast("오늘의 지지를 보냈어요.");

    // 그룹 정보 다시 불러오기
    const groupRes = await fetch(`/api/v1/support/group/${groupId}/settings`);
    if (groupRes.ok) {
      const groupData = await groupRes.json();
      const groupInfo = groupData.group;

      // DOM 업데이트
      card.querySelector("[data-stat='exp']").textContent = `경험치 · ${groupInfo.exp}회`;
      card.querySelector("[data-stat='streak']").textContent = `연속 지지 스트릭 · ${groupInfo.streak}일`;
      card.querySelector("[data-stat='max-streak']").textContent = `최고 기록 ${groupInfo.max_streak}일`;
    }
  } catch (error) {
    console.error("지지하기 요청 실패:", error);
  }
}


async function loadGroups() {
  if (loading) return;
  loading = true;
  try {
    // 첫 로딩 시 기존 하드코딩 제거
    // if (groupOffset === 0) {
    //   groupList.innerHTML = ""; 
    // }
    const res = await fetch(`/api/v1/support/groups?group_limit=${groupLimit}&group_offset=${groupOffset}`);
    const data = await res.json();
    data.groups.forEach(item => {
      const group = item.group;
      const members = item.members;

      // 카드 생성
      const card = document.createElement("article");
      card.className = "card group-card";
      card.innerHTML = `
        <div class="group-card-header">
          <div class="group-title"><strong>${group.name}</strong></div>
          <div class="group-actions">
            <span class="group-type badge">${group.group_type}</span>
            <a href="/pages/support/manage.html?group_id=${group.id}" 
              class="btn btn-outline btn-sm">모임 관리</a>
          </div>
        </div>
        <div class="group-stats">
          <div class="stat-box">
            <div class="stat-row">
              <span class="stat-icon">🌳</span>
              <div>
                <div class="stat-main" data-stat="exp">경험치 · ${group.exp}회</div>
                <div class="stat-sub">다음 레벨까지는 추후 계산</div>
              </div>
            </div>
          </div>
          <div class="stat-box">
            <div class="stat-row">
              <span class="stat-icon">🔥</span>
              <div>
                <div class="stat-main" data-stat="streak">연속 지지 스트릭 · ${group.streak}일</div>
                <div class="stat-sub" data-stat="max-streak">최고 기록 ${group.max_streak}일</div>
              </div>
            </div>
          </div>
        </div>
      `;

      // 멤버 리스트
      const memberList = document.createElement("div");
      memberList.className = "member-list";
      members.forEach(m => {
        const nickname = m.nickname || "익명";
        const firstChar = nickname.charAt(0);
        const rate = m.complete_rate || 0;
        const barColor = rate >= 100 ? "green" : "blue";

        const row = document.createElement("div");
        row.className = "member-row";

        const button = document.createElement("button");
        button.type = "button";
        button.className = "btn btn-outline btn-sm";
        button.dataset.supportButton = true;
        button.textContent = m.supported_today ? "오늘 지지 완료" : "지지하기";
        button.disabled = m.supported_today;

        // 클릭 이벤트 연결
        button.addEventListener("click", () => {
          sendSupport(group.id, m.user_id, button, card);
        });

        row.innerHTML = `
          <div class="member-avatar">${firstChar}</div>
          <div class="member-info">
            <div class="member-name">${nickname}님</div>
            <div class="member-progress">
              <div class="progress-bar ${barColor}" style="width:${rate}%;"></div>
            </div>
          </div>
        `;
        row.appendChild(button);
        memberList.appendChild(row);

      });

      card.appendChild(memberList);
      groupList.appendChild(card);
    });

    groupOffset += groupLimit;
  } catch (err) {
    console.error("그룹 불러오기 실패:", err);
  } finally {
    loading = false;
  }
}

// 첫 로딩
loadGroups();

// 스크롤 이벤트로 추가 로딩
window.addEventListener("scroll", () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 200) {
    loadGroups();
  }
});
// =============그룹 리스트 출력 완 =============