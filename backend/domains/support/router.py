from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from . import schemas, service
from backend.database import get_db
from backend.domains.auth.router import get_current_user

router = APIRouter()

# TODO : 지지하기 후에 갱신 로직 넣기

# ============== 12-ex1 모임 가입하기 ========================

# 코드 입력시 모임 정보 가져오기
@router.get("/group/summary/{invite_code}", response_model=schemas.GroupSummary)
def group_summary(
    invite_code: str,
    db: Session = Depends(get_db),
    current_user : int = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(ge=0)
):
    try:
        return service.group_summary_service(db, invite_code, current_user.id, limit, offset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# 코드로 모임 참여하기
@router.post("/group/invite/{invite_code}", response_model=schemas.InviteResponse)
def join_group_by_invite(
    invite_code: str,
    db : Session = Depends(get_db),
    current_user : int = Depends(get_current_user)):
    
    try:
        return service.invited_group_service(db, invite_code, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# ============== 12 지지 ========================

# 모임 읽어오기 (모임명, 모임종류, 경험치, 스트릭, 맴버별(닉네임, 달성율))
@router.get("/groups", response_model=schemas.GroupsResponse)
def my_groups(
    db: Session = Depends(get_db),
    current_user : int = Depends(get_current_user),
    group_limit: int = Query(3, ge=0),
    group_offset: int = Query(ge=0),
    member_limit: int = Query(10, ge=0, le=100),
    member_offset: int = Query(ge=0)
):
    
    try:
        return service.groups_info_service(db, current_user.id, group_limit, group_offset, member_limit, member_offset)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# 지지하기
@router.post("/group/{group_id}/support/{to_user_id}", response_model=schemas.SupportResponse)
def send_support(
    group_id: int,
    to_user_id: int,
    db: Session = Depends(get_db),
    current_user : int = Depends(get_current_user)
):
    
    try:
        return service.send_support_service(db, group_id, current_user.id, to_user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# =============== 12-1 모임 만들기 ====================

# 모임 생성
@router.post("/group/create", response_model=schemas.GroupCreateResponse)
def create_group(
    group: schemas.GroupCreate,
    db: Session = Depends(get_db),
    current_user : int = Depends(get_current_user)
):
    
    return service.create_group_service(db, group, user_id = current_user.id)


# =============== 12-2 모임 관리 ====================
# 모임 정보 수정하기
@router.put("/group/{group_id}/profile", response_model=schemas.UpdateGroupResponse)
def update_group_profile(
    group_id: int,
    group: schemas.GroupCreate,
    db: Session = Depends(get_db),
    current_user : int = Depends(get_current_user)
):
    
    try:
        return service.update_group_profile_service(db, group_id, current_user.id, group)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# 모임 읽어오기 (모임명, 모임 종류, 초대코드, 습관)
@router.get("/group/{group_id}/settings", response_model=schemas.GroupSettingsResponse)
def group_settings(
    group_id: int,
    db: Session = Depends(get_db),
    current_user : int = Depends(get_current_user)
):
    
    try:
        return service.group_settings_service(db, group_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# 모임 탈퇴하기
@router.delete("/group/{group_id}/leave", response_model=schemas.LeaveResponse)
def leave_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user : int = Depends(get_current_user)
):
    
    try:
        return service.leave_group_service(db, group_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    

# ================13-1 모임 구해요=================

# 함께하기로 모임 참가
@router.post("/group/post/{post_id}", response_model=schemas.JoinByPostResponse)
def join_group_by_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user : int = Depends(get_current_user)
):
    
    try:
        return service.join_by_post_service(db, post_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ================= 알림 =========================
@router.get("/notifications/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    return service.unread_notifications_service(db, current_user.id)
