// ============ 페이지 로드 =================
document.addEventListener("DOMContentLoaded", () => {
  requireLogin();
  loadGroupSettings();
});

const params = new URLSearchParams(window.location.search);
const groupId = params.get("group_id");

async function loadGroupSettings() {
  try {
    // 모임 설정 불러오기
    const data = await apiGet(`/support/group/${groupId}/settings`);

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

    // 함께하는 습관 표시
    if (group.habit && group.frequency) {
      const habitBox = document.createElement("div");
      habitBox.style.marginTop = "0.75rem";
      habitBox.innerHTML = `
        <div style="font-size:0.75rem;font-weight:500;margin-bottom:0.4rem;">함께하는 습관</div>
        <input id="group-habit" class="inp habit-field" value="${group.habit} · ${group.frequency}" disabled>
      `;
      const groupInfoBox = document.querySelector(".group-info-box");
      const saveBtnBox = groupInfoBox.querySelector(".page-actions");
      groupInfoBox.insertBefore(habitBox, saveBtnBox);
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

      try {
        await apiPut(`/support/group/${groupId}/profile`, { name: newName, group_type: newType });
        showToast("모임 정보가 저장되었습니다.");
      } catch (err) {
        showToast(err.message || "저장 실패");
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

    // 탈퇴 버튼 이벤트
    const leaveBtn = document.querySelector(".page-actions .btn-outline");
    leaveBtn.addEventListener("click", async () => {
      if (!confirm("정말 탈퇴하시겠습니까?")) return;
      try {
        await apiDelete(`/support/group/${groupId}/leave`);
        showToast("모임에서 탈퇴했습니다.");
        window.location.href = PAGES.support;
      } catch (err) {
        showToast(err.message || "탈퇴 실패");
      }
    });

  } catch (err) {
    showToast(err.message || "모임 설정 불러오기 실패");
  }
}

