// ============ 페이지 로드 =================
document.addEventListener("DOMContentLoaded", () => {
  requireLogin();
  loadGroups();
});

// =============그룹 리스트 출력===============
const groupList = document.querySelector(".group-list");
let groupOffset = 0;
const groupLimit = 3;
let loading = false;
let hasMore = true;

// 경험치 단계 계산 함수
function getLevelInfo(exp) {
  if (exp < 50) {
    return { name: "씨앗", icon: "🌱", next: 50 - exp };
  } else if (exp < 100) {
    return { name: "새싹", icon: "🌿", next: 100 - exp };
  } else if (exp < 150) {
    return { name: "가지", icon: "🍃", next: 150 - exp };
  } else if (exp < 200) {
    return { name: "열매", icon: "🍎", next: 200 - exp };
  } else {
    return { name: "나무", icon: "🌳", next: null }; // 최대 레벨
  }
}

// JWT에서 현재 사용자 ID 추출
function getCurrentUserId() {
  const token = localStorage.getItem("gigi_token");
  if (!token) return null;

  try {
    const payloadBase64 = token.split(".")[1];
    const payloadJson = atob(payloadBase64);
    const payload = JSON.parse(payloadJson);

    return parseInt(payload.sub, 10);
  } catch (err) {
    console.error("토큰 파싱 실패:", err);
    return null;
  }
}

async function sendSupport(groupId, toUserId, button, card) {
  try {
    const token = localStorage.getItem("gigi_token");
    const res = await fetch(`/api/v1/support/group/${groupId}/support/${toUserId}`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });
    if (!res.ok) {
      const err = await res.json();
      showToast(err.detail || "지지 실패");
      return;
    }
    
    // 그룹 정보 갱신
    const groupData = await res.json();
    const groupInfo = groupData.group;
    const level = getLevelInfo(groupInfo.exp);

    card.querySelector("[data-stat='exp']").textContent =
      `${level.icon} ${level.name} · 경험치 ${groupInfo.exp}회`;

    if (level.next !== null) {
      card.querySelector(".stat-sub").textContent =
        `다음 레벨까지 ${level.next}회 남음`;
    } else {
      card.querySelector(".stat-sub").textContent = "최대 레벨입니다.";
    }
    card.querySelector("[data-stat='streak']").textContent = `연속 지지 스트릭 · ${groupInfo.streak}일`;
    card.querySelector("[data-stat='max-streak']").textContent = `최고 기록 ${groupInfo.max_streak}일`;    

    button.disabled = true;
    button.textContent = "오늘 지지 완료";
    showToast("오늘의 지지를 보냈어요.");

  } catch (error) {
    console.error("지지하기 요청 실패:", error);
  }
}

async function loadGroups() {
  if (loading || !hasMore) return;
  loading = true;
  try {
    if (groupOffset === 0) {
      groupList.innerHTML = ""; 
    }
    const token = localStorage.getItem("gigi_token");
    const res = await fetch(`/api/v1/support/groups?group_limit=${groupLimit}&group_offset=${groupOffset}`, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });
    if (!res.ok) {
      console.error("그룹 불러오기 실패:", await res.text());
      return;
    }
    const data = await res.json();

    // 데이터 없으면 기본 카드 표시
    if (!data.groups || data.groups.length === 0) {
      hasMore = false;
      if (groupOffset === 0) {
        const card = document.createElement("article");
        card.className = "card group-card";
        card.innerHTML = `
          <div class="group-card-header">
            <div class="group-title"><strong>가입한 그룹이 없어요</strong></div>
          </div>
        `;
        groupList.appendChild(card);
      }
      return;
    }

    // 그룹 있을 때 카드 렌더링
    data.groups.forEach(item => {
      const group = item.group;
      const members = item.members;

      const card = document.createElement("article");
      card.className = "card group-card";

      // 기본 헤더
      card.innerHTML = `
        <div class="group-card-header">
          <div class="group-title"><strong>${group.name}</strong></div>
          <div class="group-actions">
            <span class="group-type badge">${group.group_type}</span>
            <a href="/pages/support/manage.html?group_id=${group.id}" 
              class="btn btn-outline btn-sm">모임 관리</a>
          </div>
        </div>
      `;

      // 📌 함께하는 습관 표시 (habit + frequency 있을 때만)
      if (group.habit && group.frequency) {
        const habitBox = document.createElement("div");
        habitBox.className = "habit-box";
        habitBox.textContent = `📌 함께하는 습관: ${group.habit} · ${group.frequency}`;
        card.appendChild(habitBox);
      }

      // 그룹 통계
      const stats = document.createElement("div");
      stats.className = "group-stats";

      const level = getLevelInfo(group.exp);

      stats.innerHTML = `
        <div class="stat-box">
          <div class="stat-row">
            <span class="stat-icon">${level.icon}</span>
            <div>
              <div class="stat-main" data-stat="exp">${level.icon} ${level.name} · 경험치 ${group.exp}회</div>
              <div class="stat-sub">
                ${level.next !== null ? `다음 레벨까지 ${level.next}회 남음` : "최대 레벨입니다."}
              </div>
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
      `;
      card.appendChild(stats);

      const memberList = document.createElement("div");
      memberList.className = "member-list";

      const currentUserId = getCurrentUserId();

      if (!members || members.length === 0) {
        // 멤버가 없을 때 안내 문구 표시
        const emptyRow = document.createElement("div");
        emptyRow.className = "member-row empty";
        emptyRow.textContent = "이 그룹엔 나밖에 없어요";
        memberList.appendChild(emptyRow);
      } else {
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

          // 내 기록일 경우 버튼 숨김
          if (m.user_id === currentUserId) {
            button.style.display = "none";
          } else {
            button.dataset.supportButton = true;
            button.textContent = m.supported_today ? "오늘 지지 완료" : "지지하기";
            button.disabled = m.supported_today;
            button.addEventListener("click", () => {
              sendSupport(group.id, m.user_id, button, card);
            });
          }

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
          
          // 드롭다운메뉴 호출
          attachMemberClick(row, m.user_id);
        });
      }

      card.appendChild(memberList);
      groupList.appendChild(card);
    });

    groupOffset += groupLimit;

    // 마지막 페이지 확인
    if (data.groups.length < groupLimit) {
      hasMore = false;
    }    
  } catch (err) {
    console.error("그룹 불러오기 실패:", err);
  } finally {
    loading = false;
  }
}

function attachMemberClick(row, userId) {
  row.addEventListener("click", async () => {
    let dropdown = row.nextElementSibling;
    if (dropdown && dropdown.classList.contains("habit-dropdown")) {
      dropdown.classList.toggle("open");
      if (!dropdown.classList.contains("open")) {
        dropdown.remove();
      }
      return;
    }

    try {
      const token = localStorage.getItem("gigi_token");
      const res = await fetch(`/api/v1/support/habits/${userId}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!res.ok) {
        showToast("습관 불러오기 실패");
        return;
      }
      const data = await res.json();

      dropdown = document.createElement("div");
      dropdown.className = "habit-dropdown open";

      if (!data.habits || data.habits.length === 0) {
        dropdown.textContent = "습관이 없습니다.";
      } else {
        data.habits.forEach(habit => {
          const item = document.createElement("div");
          item.className = "habit-row";
          item.innerHTML = `
            <span class="habit-title">${habit.title}</span>
            <span class="habit-category">${habit.category}</span>
            <span class="chk-box ${habit.is_checked ? "done" : ""}"></span>
          `;
          dropdown.appendChild(item);
        });
      }

      row.insertAdjacentElement("afterend", dropdown);
    } catch (err) {
      console.error("습관 불러오기 실패:", err);
    }
  });
}

window.addEventListener("scroll", () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 200) {
    loadGroups();
  }
});
