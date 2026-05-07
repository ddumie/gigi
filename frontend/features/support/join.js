document.addEventListener("DOMContentLoaded", () => {
  requireLogin();

  const $codeInput = document.getElementById("invite-code");
  const $summaryBox = document.getElementById("group-summary");
  const $joinBtn = document.getElementById("join-group-btn");

  // 코드 입력 후 포커스 아웃 시 모임 정보 조회
  $codeInput.addEventListener("blur", async () => {
    const code = $codeInput.value.trim();
    if (!code) return;

    try {
      const res = await apiGet(`/support/group/summary/${code}`);
      $summaryBox.innerHTML = `
        <div><strong>${res.name}</strong> (${res.group_type})</div>
        <div>멤버: ${res.members.join(", ")}</div>
      `;

      if (res.already_joined) {
        $joinBtn.disabled = true;
        $joinBtn.textContent = "이미 가입한 모임입니다";
      } else {
        $joinBtn.disabled = false;
        $joinBtn.textContent = "모임 가입하기";
        $joinBtn.dataset.inviteCode = code;
      }
    } catch (err) {
      $summaryBox.innerHTML = `<span class="error">코드가 잘못되었거나 만료되었습니다.</span>`;
      $joinBtn.disabled = true;
    }
  });

  // 가입 버튼 클릭 시
  $joinBtn.addEventListener("click", async () => {
    const code = $joinBtn.dataset.inviteCode;
    if (!code) return;

    try {
      await apiPost(`/support/group/invite/${code}`);
      showToast("모임에 가입했습니다.");
      window.location.href = PAGES.support;
    } catch (err) {
      showToast(err.message || "가입 실패");
    }
  });
});
