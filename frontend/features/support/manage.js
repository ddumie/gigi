// /features/support/manage.js

const params = new URLSearchParams(window.location.search);
const groupId = params.get("group_id");

async function loadGroupSettings() {
  try {
    const res = await fetch(`/api/v1/support/group/${groupId}/settings`);
    if (!res.ok) {
      console.error("그룹 설정 불러오기 실패");
      return;
    }
    const data = await res.json();
    const group = data.group;
    const members = data.members;
    const invite = data.invite;

    // 초대 코드 표시
    document.querySelector(".invite-code-box .section-title").textContent = invite.code;

    // 멤버 목록 표시
    const memberList = document.querySelector(".member-list");
    memberList.innerHTML = "";
    members.forEach(m => {
      const row = document.createElement("div");
      row.className = "member-row";
      row.innerHTML = `
        <span>${m.nickname}님</span>
        <span class="meta-text">${m.role}</span>
      `;
      memberList.appendChild(row);
    });

    // 탈퇴 버튼 연결
    const leaveBtn = document.querySelector(".page-actions .btn");
    leaveBtn.addEventListener("click", async () => {
      if (!confirm("정말 탈퇴하시겠습니까?")) return;
      const leaveRes = await fetch(`/api/v1/support/group/${groupId}/leave`, {
        method: "POST"
      });
      if (leaveRes.ok) {
        showToast("모임에서 탈퇴했습니다.");
        window.location.href = "/pages/support/index.html";
      } else {
        showToast("탈퇴 실패");
      }
    });
  } catch (err) {
    console.error("manage.js 오류:", err);
  }
}

// 첫 로딩
loadGroupSettings();
