from sqlalchemy.ext.asyncio import AsyncSession
from . import crud, schemas

# 초대코드로 모임 정보 조회
async def group_summary_service(db: AsyncSession, invite_code: str, user_id: int, limit: int = 10, offset: int = 0):
    result = await crud.get_group_summary(db, invite_code, limit, offset)
    if not result:
        raise ValueError("초대코드가 잘못 되었거나 만료되었습니다.")
    
    group, nicknames, member_ids = result
    already_joined = user_id in member_ids

    return {
        "id": group.id,
        "name": group.name,
        "group_type": group.group_type,
        "members": nicknames,
        "already_joined": already_joined
    }

# 초대코드로 모임 가입
async def invited_group_service(db: AsyncSession, invite_code: str, user_id: int):
    group_id = await crud.get_group_id_by_code(db, invite_code)
    if not group_id:
        raise ValueError("초대코드가 잘못 되었거나 만료 되었습니다.")
    new_member = await join_group_service(db, group_id, user_id)
    return {"message": "초대코드로 모임 가입", "group_id": new_member.group_id, "user_id": new_member.user_id}

# 모임 생성
async def create_group_service(db: AsyncSession, group: schemas.GroupCreate, user_id: int):
    try:
        db_group = await crud.create_group(db, group, user_id)
        if not db_group:
            raise ValueError("모임 생성에 실패 했습니다.")
        await join_group_service(db, db_group.id, user_id)
        return {"id": db_group.id}
    except Exception as e:
        raise e

# 모임 목록 출력
async def groups_info_service(
    db: AsyncSession,
    user_id: int,
    group_limit: int = 3,
    group_offset: int = 0,
    member_limit: int = 10,
    member_offset: int = 0
):
    group_rows = await crud.get_group_ids_by_uid(db, user_id, group_limit, group_offset)
    results = []

    for idx, row in enumerate(group_rows):
        gid = row["group_id"]

        # 멤버 조회 (닉네임 포함)
        members_rows = await crud.get_group_members(db, gid, member_limit, member_offset, exclude_user_id=user_id)
        members = [row["GroupMember"] for row in members_rows]
        member_nicknames = {row["GroupMember"].user_id: row["nickname"] for row in members_rows}

        # 첫 번째 모임이고 첫 페이지일 때 본인을 맨 앞에 추가
        if idx == 0 and group_offset == 0:
            my_member = await crud.get_me(db, gid, user_id)
            if my_member:
                members = [my_member] + members
                user = await crud.get_user_by_id(db, user_id)
                if user:
                    member_nicknames[my_member.user_id] = user.nickname

        # 달성률 계산
        achievement_rates = await crud.get_members_achievement(db, members)

        # 맴버별 마지막 습관 체크일 호출
        last_activity = await crud.get_members_last_activity(db, members)

        # 오늘 내 지지 기록 -> 없으면 오늘 모임 기록 -> 없으면 어제 모임 기록 -> 없으면 0으로 초기화
        supports_today = await crud.check_my_support(db, gid, user_id)
        if not supports_today and row["support_streak"]:
            group_supports_today = await crud.check_group_support(db, gid)
            if not group_supports_today:
                supports_yesterday = await crud.check_group_support_yesterday(db, gid)
                if not supports_yesterday:
                    await crud.reset_group_streak(db, gid)

        supported_map = {s.to_user_id: True for s in supports_today}

        results.append({
            "group": {
                "id": gid,
                "name": row["name"],
                "group_type": row["group_type"],
                "exp": row["total_support_count"],
                "streak": row["support_streak"],
                "max_streak": row["max_streak"],
                "habit": row["habit_title"],      
                "frequency": row["frequency"]     
            },
            "members": [
                {
                    "user_id": m.user_id,
                    "nickname": member_nicknames.get(m.user_id),
                    "complete_rate": achievement_rates.get(m.user_id),
                    "supported_today": supported_map.get(m.user_id, False),
                    "last_activity": last_activity.get(m.user_id)
                }
                for m in members
            ]
        })

    return {"groups": results}

# 모임 관리
async def group_settings_service(db: AsyncSession, group_id: int, user_id: int):
    group, groupprofile, invite, members, habit_info, member_top_exp, member_nicknames = await crud.get_group_4_settings(db, group_id, user_id)
    if not group:
        raise ValueError("모임을 찾을 수 없습니다.")
    if not invite:
        raise ValueError("초대코드를 찾을 수 없습니다.")
    if not members:
        raise ValueError("해당 모임에 맴버가 없습니다.")
    return {
        "group": {
            "id": (groupprofile.group_id if groupprofile else group.id),
            "name": (groupprofile.name if groupprofile else group.name),
            "group_type": (groupprofile.group_type if groupprofile else group.group_type),
            "habit": habit_info["habit_title"] if habit_info else None,
            "frequency": habit_info["frequency"] if habit_info else None
        },
        "invite": {"code": invite.code},
        "members": [
            {
                "id": m.id,
                "nickname": member_nicknames.get(m.user_id),
                "top_exp": member_top_exp.get(m.user_id)
            }
            for m in members
        ]
    }

# 모임 구해요로 모임 가입하기
async def join_by_post_service(db: AsyncSession, post_id: int, user_id: int):
    group_id = await crud.get_or_create_group_id_by_post(db, post_id, user_id)
    if not group_id:
        raise ValueError("해당 post_id에 연결 된 모임을 찾을 수 없습니다.")
    new_member = await join_group_service(db, group_id, user_id)
    return {"message": "모임에 참여했습니다.", "group_id": new_member.group_id, "user_id": new_member.user_id}

# 가져온 모임 id로 가입하기
async def join_group_service(db: AsyncSession, group_id: int, user_id: int):
    group = await crud.get_group_by_id(db, group_id)
    if not group:
        raise ValueError("모임을 찾을 수 없습니다.")

    existing_member = await crud.get_group_member(db, group_id, user_id)
    if existing_member:
        raise ValueError("이미 모임에 가입 된 사용자입니다.")
    new_member = await crud.add_group_member(db, group_id, user_id)    
    return new_member

# 모임 탈퇴하기
async def leave_group_service(db: AsyncSession, group_id: int, user_id: int):
    group = await crud.get_group_by_id(db, group_id)
    if not group:
        raise ValueError("모임을 찾을 수 없습니다.")
    
    member = await crud.get_group_member(db, group_id, user_id)
    if not member:
        raise ValueError("가입된 사용자가 아닙니다.")
    
    await crud.remove_group_member(db, group_id, user_id)
    return {"message": "모임에서 탈퇴했습니다.", "group_id": group_id, "user_id": user_id}

# 모임 정보 수정
async def update_group_profile_service(db: AsyncSession, group_id: int, user_id: int, group: schemas.GroupCreate):
    updated_profile = await crud.update_group_profile(db, group_id, user_id, group)
    if not updated_profile:
        raise ValueError("해당 사용자에 대한 모임 프로필을 찾을 수 없습니다.")
    return {
        "id": updated_profile.group_id,
        "name": updated_profile.name,
        "group_type": updated_profile.group_type
    }

# 지지하기 알림
async def send_support_service(db: AsyncSession, group_id: int, from_user_id: int, to_user_id: int):
    # 셀프 지지 방지
    if from_user_id == to_user_id:
        raise ValueError("자기 자신은 지지 할 수 없습니다.")

    # 모임 멤버 여부 확인
    member = await crud.get_group_member(db, group_id, to_user_id)
    if not member:
        raise ValueError("해당 모임에 가입된 사용자만 지지할 수 있습니다.")

    # 1일 1회 제한 체크
    existing = await crud.check_support_exists(db, group_id, from_user_id, to_user_id)
    if existing:
        raise ValueError("오늘은 이미 지지했습니다.")

    # Support 생성
    support = await crud.create_support(db, group_id, from_user_id, to_user_id)

    # 알림 생성
    from_user = await crud.get_user_by_id(db, from_user_id)
    content = f"{from_user.nickname}님이 지지를 보냈어요!"
    notification = await crud.create_notification(db, to_user_id, "support", content)

    # 모임 정보 갱신
    group = await crud.get_group_by_id(db, group_id)
    if not group:
        raise ValueError("모임을 찾을 수 없습니다.")

    return {
        "group": {
            "exp": group.total_support_count,
            "streak": group.support_streak,
            "max_streak": group.max_streak,            
        },
        "message": "지지를 보냈습니다.",
        "support_id": support.id,
        "notification_id": notification.id
    }


# 안 읽은 알림 개수 조회
async def unread_notifications_service(db: AsyncSession, user_id: int):
    # 안 읽은 알림 개수 가져오기
    count = await crud.get_unread_notification_count(db, user_id)
    return {"count": count}


# 최근 알림 리스트 조회
async def recent_notifications_service(db: AsyncSession, user_id: int, limit: int = 3):
    items = await crud.get_recent_notifications(db, user_id, limit)
    return {
        "notifications": [
            {
                "id": n.id,
                "type": n.type,
                "content": n.content,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else "",
            }
            for n in items
        ]
    }


# 안 읽은 알림 전부 읽음 처리
async def mark_notifications_read_service(db: AsyncSession, user_id: int):
    updated = await crud.mark_all_notifications_read(db, user_id)
    return {"updated": updated}

# 개별 인원 습관 달성 여부 호출
async def get_habits_service(db: AsyncSession, user_id: int):
    habits = await crud.get_personal_habits(db, user_id)

    return {
        "habits": [
            {
                "title": h["title"],
                "category": h["category"],
                "is_checked": h["is_checked"]
            }
            for h in habits
        ]
    }
