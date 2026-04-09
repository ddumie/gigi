from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import schemas, service
from backend.database import get_db

router = APIRouter()

CUI = 1 # TODO auth 모듈 완료 되면 반드시 고칠 것!
# ============== 12 지지 ========================
# 코드로 모임 참여하기
@router.post("/group/invite/{invite_code}")
def invited_group(
    invite_code: str,
    db: Session = Depends(get_db),
    current_user_id: int = CUI
):
    try:
        new_member = service.invited_group_service(db, invite_code, current_user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "초대코드로 그룹 가입", "group_id": new_member.group_id, "user_id": new_member.user_id}

# 모임 읽어오기 (모임명, 모임 종류, 초대코드, 습관) (12-2 모임관리에서도 이용)
@router.get("/group/{group_id}/info")
def group_info(
    group_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = CUI
):
    try:
        group, groupprofile, invite, members, habit_info = service.group_info_service(db, group_id, current_user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "group": {
            "id": groupprofile.group_id,
            "name": groupprofile.name,
            "group_type": groupprofile.group_type,
            "exp": group.total_support_count,
            "streak": group.support_streak,
            "habit": habit_info["habit_title"] if habit_info else None,
            "frequency": habit_info["frequency"] if habit_info else None
        },
        "invite": {"code": invite.code},
        "members": [{"id": m.id, "user_id": m.user_id, "joined_at": m.joined_at} for m in members]
    }


# =============== 12-1 모임 만들기 ====================

# 모임 생성
@router.post("/group/create")
def create_group(
    group: schemas.GroupCreate,
    db: Session = Depends(get_db),
    current_user_id: int = CUI
):
    db_group = service.create_group_service(db, group, user_id = current_user_id)
    return {"group" : {"id": db_group.id}}


# =============== 12-2 모임 관리 ====================
# 모임 정보 수정하기
@router.put("/group/{group_id}/profile")
def update_group_profile(
    group_id: int,
    group: schemas.GroupCreate,
    db: Session = Depends(get_db),
    current_user_id: int = CUI
):
    try:
        updated_profile = service.update_group_profile_service(db, group_id, current_user_id, group)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "message": "모임 정보가 수정되었습니다.",
        "group": {
            "id": updated_profile.group_id,
            "name": updated_profile.name,
            "group_type": updated_profile.group_type
        }
    }

# 모임 탈퇴하기
@router.delete("/group/{group_id}/leave")
def leave_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = CUI
):
    try:
        member = service.leave_group_service(db, group_id, current_user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "모임에서 탈퇴했습니다.", "group_id":group_id, "user_id":current_user_id}


# ================13-1 모임 구해요=================

# 함께하기로 모임 참가
@router.post("/group/post/{post_id}")
def join_group(
    post_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = CUI
):
    try:
        new_member = service.join_by_post_service(db, post_id, current_user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "함께하기로 모임 가입", "group_id": new_member.group_id, "user_id": new_member.user_id}