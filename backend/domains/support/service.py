from sqlalchemy.orm import Session
from . import crud, schemas

# 초대코드로 그룹 정보 조회
def group_summary_service(db: Session, invite_code: str, limit: int = 10, offset: int = 0):
    result = crud.get_group_summary(db, invite_code, limit, offset)
    if not result:
        raise ValueError("초대코드가 잘못 되었거나 만료되었습니다.")
    
    group, nicknames = result

    return {
        "id": group.id,
        "name": group.name,
        "group_type": group.group_type,
        "members": nicknames
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
    # 사용자가 가입한 모든 그룹 id 가져오기
    group_ids = crud.get_group_ids_by_uid(db, user_id, group_limit, group_offset)
    results = []
    for gid_tuple in group_ids:
        gid = gid_tuple[0]
        group, groupprofile, invite, members, habit_info, member_top_exp, member_nicknames, complete_rates = crud.get_group(db, gid, user_id, member_limit, member_offset)
        supports_today = crud.check_group_support(db, gid, user_id)
        supported_map = {s.to_user_id: True for s in supports_today}
        if not group:
            raise ValueError("모임을 찾을 수 없습니다.")
        if not groupprofile:
            raise ValueError("모임 설정을 찾을 수 없습니다.")
        if not invite:
            raise ValueError("초대코드를 찾을 수 없습니다.")
        if not members:
            raise ValueError("해당 그룹에 맴버가 없습니다.")
        results.append({
            "group": {
                "id": groupprofile.group_id,
                "name": groupprofile.name,
                "group_type": groupprofile.group_type,
                "exp": group.total_support_count,
                "streak": group.support_streak,
                "max_streak": group.max_streak,
                "habit": habit_info["habit_title"] if habit_info else None,
                "frequency": habit_info["frequency"] if habit_info else None
            },
            "invite": {"code": invite.code},
            "members": [
                {
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
    group, groupprofile, invite, members, habit_info, member_top_exp, member_nicknames, complete_rates = crud.get_group(db, group_id, user_id)
    if not group:
        raise ValueError("모임을 찾을 수 없습니다.")
    if not groupprofile:
        raise ValueError("모임 설정을 찾을 수 없습니다.")
    if not invite:
        raise ValueError("초대코드를 찾을 수 없습니다.")
    if not members:
        raise ValueError("해당 그룹에 맴버가 없습니다.")
    return {
        "group": {
            "id": groupprofile.group_id,
            "name": groupprofile.name,
            "group_type": groupprofile.group_type,
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

    return {
        "message": "지지를 보냈습니다.",
        "support_id": support.id,
        "notification_id": notification.id
    }