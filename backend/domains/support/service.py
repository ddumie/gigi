from sqlalchemy.orm import Session
from . import crud, schemas

# 초대코드로 그룹 정보 조회
def group_summary_service(db: Session, invite_code: str, user_id: int, limit: int = 10, offset: int = 0):
    result = crud.get_group_summary(db, invite_code, limit, offset)
    if not result:
        raise ValueError("초대코드가 잘못 되었거나 만료되었습니다.")
    
    group, nicknames, member_ids = result  # member_ids도 반환하도록 crud 수정

    already_joined = user_id in member_ids

    return {
        "id": group.id,
        "name": group.name,
        "group_type": group.group_type,
        "members": nicknames,
        "already_joined": already_joined
    }

# 초대코드로 모임 가입
def invited_group_service(db: Session, invite_code: str, user_id: int):
    group_id = crud.get_group_id_by_code(db, invite_code)
    if not group_id:
        raise ValueError("초대코드가 잘못 되었거나 만료 되었습니다.")
    new_member = join_group_service(db, group_id, user_id)
    return {"message": "초대코드로 그룹 가입", "group_id": new_member.group_id, "user_id": new_member.user_id}

# 모임 생성
def create_group_service(db: Session, group: schemas.GroupCreate, user_id: int):
    db_group = crud.create_group(db, group, user_id)

    join_group_service(db, db_group.id, user_id)
    return {"id": db_group.id}

# 모임 목록 출력
def groups_info_service(
    db: Session,
    user_id: int,
    group_limit: int = 3,
    group_offset: int = 0,
    member_limit: int = 10,
    member_offset: int = 0
):
    group_ids = crud.get_group_ids_by_uid(db, user_id, group_limit, group_offset)
    results = []

    for idx, gid_tuple in enumerate(group_ids):
        gid = gid_tuple[0]

        # 첫 그룹 첫 조회: 내 기록 + 9명
        if idx == 0 and group_offset == 0:
            my_member = crud.get_me(db, gid, user_id)
            members = crud.get_group_members(db, gid, 9, member_offset, user_id=user_id)
            if my_member:
                members = [my_member] + members
        else:
            if idx == 0:
                members = crud.get_group_members(db, gid, member_limit, member_offset - 1, user_id=user_id)
            else:                
                members = crud.get_group_members(db, gid, member_limit, member_offset, user_id=user_id)

        group, groupprofile, invite, habit_info = crud.get_group(db, gid, user_id)
        supports_today = crud.check_group_support(db, gid, user_id)

        if not supports_today:
            streak_value = group.support_streak or 0
            if streak_value != 0:
                supports_yesterday = crud.check_group_support_yesterday(db, gid, user_id)
                if not supports_yesterday:
                    crud.reset_group_streak(db, gid)

        supported_map = {s.to_user_id: True for s in supports_today}

        # 닉네임/달성률은 crud에서 계산
        member_nicknames, complete_rates = crud.get_members_info(db, members)

        if not group:
            raise ValueError("모임을 찾을 수 없습니다.")
        if not invite:
            raise ValueError("초대코드를 찾을 수 없습니다.")

        results.append({
            "group": {
                "id": (groupprofile.group_id if groupprofile else group.id),
                "name": (groupprofile.name if groupprofile else group.name),
                "group_type": (groupprofile.group_type if groupprofile else group.group_type),
                "exp": group.total_support_count,
                "streak": group.support_streak,
                "max_streak": group.max_streak,
                "habit": habit_info["habit_title"] if habit_info else None,
                "frequency": habit_info["frequency"] if habit_info else None
            },
            "members": [
                {
                    "user_id": m.user_id,
                    "nickname": member_nicknames.get(m.user_id),
                    "complete_rate": complete_rates.get(m.user_id),
                    "supported_today": supported_map.get(m.user_id, False)
                }
                for m in members
            ]
        })

    return {"groups": results}

# 모임 관리
def group_settings_service(db: Session, group_id: int, user_id: int):
    group, groupprofile, invite, members, habit_info, member_top_exp, member_nicknames = crud.get_group_4_settings(db, group_id, user_id)
    if not group:
        raise ValueError("모임을 찾을 수 없습니다.")
    # if not groupprofile:
    #     raise ValueError("모임 설정을 찾을 수 없습니다.")
    if not invite:
        raise ValueError("초대코드를 찾을 수 없습니다.")
    if not members:
        raise ValueError("해당 그룹에 맴버가 없습니다.")
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
def join_by_post_service(db: Session, post_id: int, user_id: int):
    group_id = crud.get_or_create_group_id_by_post(db, post_id, user_id)
    if not group_id:
        raise ValueError("해당 post_id에 연결 된 그룹을 찾을 수 없습니다.")
    new_member = join_group_service(db, group_id, user_id)
    return {"group_id": new_member.group_id, "user_id": new_member.user_id}

# 가져온 그룹 id로 가입하기
def join_group_service(db: Session, group_id: int, user_id: int):
    # 모임 존재 확인
    group = crud.get_group_by_id(db, group_id)
    if not group:
        raise ValueError("모임을 찾을 수 없습니다.")

    # 중복가입 확인
    existing_member = crud.get_group_member(db, group_id, user_id)
    if existing_member:
        raise ValueError("이미 모임에 가입 된 사용자입니다.")
    new_member = crud.add_group_member(db, group_id, user_id)    
    return new_member

# 모임 탈퇴하기
def leave_group_service(db: Session, group_id: int, user_id: int):
    # 모임 확인
    group = crud.get_group_by_id(db, group_id)
    if not group:
        raise ValueError("모임을 찾을 수 없습니다.")
    
    # 가입 여부 확인
    member = crud.get_group_member(db, group_id, user_id)
    if not member:
        raise ValueError("가입된 사용자가 아닙니다.")
    
    # 탈퇴처리
    crud.remove_group_member(db, group_id, user_id)
    return {"message": "모임에서 탈퇴했습니다.", "group_id":group_id, "user_id":user_id}

# 모임 정보 수정
def update_group_profile_service(db: Session, group_id: int, user_id: int, group: schemas.GroupCreate):
    updated_profile = crud.update_group_profile(db, group_id, user_id, group)
    if not updated_profile:
        raise ValueError("해당 사용자에 대한 그룹 프로필을 찾을 수 없습니다.")
    return {
        "id": updated_profile.group_id,
        "name": updated_profile.name,
        "group_type": updated_profile.group_type
    }

# 지지하기 알림
def send_support_service(db: Session, group_id: int, from_user_id: int, to_user_id: int):
    # 셀프 지지 방지
    if from_user_id == to_user_id:
        raise ValueError("자기 자신은 지지 할 수 없습니다.")

    # 그룹 멤버 여부 확인
    member = crud.get_group_member(db, group_id, to_user_id)
    if not member:
        raise ValueError("해당 그룹에 가입된 사용자만 지지할 수 있습니다.")

    # 1일 1회 제한 체크
    existing = crud.check_support_exists(db, group_id, from_user_id, to_user_id)
    if existing:
        raise ValueError("오늘은 이미 지지했습니다.")

    # Support 생성
    support = crud.create_support(db, group_id, from_user_id, to_user_id)

    # 알림 생성
    from_user = crud.get_user_by_id(db, from_user_id)

    content = f"{from_user.nickname}님이 지지를 보냈어요!"
    notification = crud.create_notification(db, to_user_id, "support", content)

    group = crud.get_group_by_id(db, group_id)
    if not group:
        raise ValueError("그룹을 찾을 수 없습니다.")

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

def unread_notifications_service(db: Session, user_id: int):
    count = crud.get_unread_notification_count(db, user_id)
    return {"count": count}
