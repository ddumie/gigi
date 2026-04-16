// =========== 로드시 ===========
document.addEventListener("DOMContentLoaded", () => {
  requireLogin();

  const $nameInput = document.getElementById("group-name");
  const $chips     = document.querySelectorAll("[data-chip-select='group-type']");
  let selectedType = null;

  // chip 선택 처리
  $chips.forEach(chip => {
    chip.addEventListener("click", () => {
      $chips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      selectedType = chip.textContent.trim();
    });
  });

  // 버튼 클릭 이벤트
  const $createBtn = document.querySelector(".btn-primary.btn-full");
  $createBtn.addEventListener("click", async (e) => {
    e.preventDefault();

    const name = $nameInput.value.trim();
    if (!name || !selectedType) {
      showToast("모임 이름과 유형을 선택해주세요.");
      return;
    }

    try {
      // 그룹 생성 API 호출
      const res = await apiPost("/support/group/create", {
        name: name,
        group_type: selectedType
      });

      showToast("모임이 생성되었습니다.");

      // 생성된 그룹 관리 페이지로 이동 (id 포함)
      window.location.href = `/pages/support/manage.html?group_id=${res.id}`;
    } catch (err) {
      showToast(err.message || "모임 생성에 실패했습니다.");
    }
  });
});
