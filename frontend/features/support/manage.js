// ============ 페이지 로드 =================
document.addEventListener("DOMContentLoaded", () => {
  requireLogin();
  loadGroupSettings();
});

const params = new URLSearchParams(window.location.search);
const groupId = params.get("group_id");

async function loadGroupSettings() {
  try {
    const token = localStorage.getItem("gigi_token");
    const res = await fetch(`/api/v1/support/group/${groupId}/settings`, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) {
      console.error("그룹 설정 불러오기 실패:", await res.text());
      return;
    }

    const data = await res.json();
    console.log("group settings 응답:", data);

    const group = data.group;
    const members = data.members;
    const invite = data.invite;

    // 초대 코드 표시
    document.querySelector(".invite-code-box .section-title").textContent = invite.code;

    // 모임 이름 표시
    document.getElementById("group-name").value = group.name;

    // 모임 유형 칩 초기화 + 클릭 이벤트
    document.querySelectorAll(".chip-group .chip").forEach(chip => {
      chip.classList.toggle("on", chip.dataset.value === group.group_type);
      chip.addEventListener("click", () => {
        document.querySelectorAll(".chip-group .chip").forEach(c => c.classList.remove("on"));
        chip.classList.add("on");
      });
    });

    // 함께하는 습관 표시 (habit, frequency가 있을 때만)
    if (group.habit && group.frequency) {
      const habitBox = document.createElement("div");
      habitBox.style.marginTop = "0.75rem";
      habitBox.innerHTML = `
        <div style="font-size:0.75rem;font-weight:500;margin-bottom:0.4rem;">함께하는 습관</div>
        <input id="group-habit" class="inp habit-field" value="${group.habit} · ${group.frequency}" disabled>
      `;
      document.querySelector(".group-info-box").appendChild(habitBox);
    }

    // 저장 버튼 이벤트 (모임 정보 수정)
    document.getElementById("save-group-btn").addEventListener("click", async () => {
      const newName = document.getElementById("group-name").value.trim();
      const selectedChip = document.querySelector(".chip-group .chip.on");
      const newType = selectedChip ? selectedChip.dataset.value : null;

      if (!newName || !newType) {
        showToast("모임 이름과 유형을 입력해주세요.");
        return;
      }

      const res = await fetch(`/api/v1/support/group/${groupId}/profile`, {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ name: newName, group_type: newType })
      });

      if (res.ok) {
        showToast("모임 정보가 저장되었습니다.");
      } else {
        showToast("저장 실패");
      }
    });

    // 멤버 목록 표시
    const memberList = document.querySelector(".member-list");
    memberList.innerHTML = "";
    members.forEach(m => {
      const row = document.createElement("div");
      row.className = "member-row";
      row.innerHTML = `
        <span>${m.nickname || "익명"}님</span>
        <span class="meta-text">${m.role || "멤버"}</span>
      `;
      memberList.appendChild(row);
    });

    // 탈퇴 버튼 이벤트 (별도)
    const leaveBtn = document.querySelector(".page-actions .btn-outline");
    leaveBtn.addEventListener("click", async () => {
      if (!confirm("정말 탈퇴하시겠습니까?")) return;
      const leaveRes = await fetch(`/api/v1/support/group/${groupId}/leave`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
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
