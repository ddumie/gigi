from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import crud, schemas, service, models
from backend.database import get_db

router = APIRouter()

# ==========예시============
# router = APIRouter(prefix="/support", tags=["support"])

# @router.post("/", response_model=schemas.SupportResponse)
# def create_support(support: schemas.SupportCreate, db: Session = Depends(get_db)):
#     return crud.create_support(db, support)

# @router.get("/feed", response_model=schemas.FeedResponse)
# def get_feed(user_id: int, db: Session = Depends(get_db)):
#     items = crud.get_feed_items(db, user_id)
#     return schemas.FeedResponse(items=items)

CUI = 1 # TODO auth 모듈 완료 되면 반드시 고칠 것!

# =============== 12-1 모임 만들기 ====================

# 모임 생성
@router.post("/group/create")
def create_group(
    group: schemas.GroupCreate,
    db: Session = Depends(get_db),
    current_user_id: int = CUI
):
    db_group = crud.create_group(db, group, user_id = current_user_id)
    return {"group" : {"id": db_group.id}}

# =============== 12-2 모임 관리 ====================

# 모임 관리 읽어오기 (모임명, 모임 종류, 초대코드)
@router.get("/group/{group_id}/setting/")
def group_setting(
    group_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = CUI
):

    groupprofile, invite = crud.get_group(db, group_id, user_id=current_user_id)

    return {
        "group": {
            "id": groupprofile.group_id,
            "name": groupprofile.name,
            "group_type": groupprofile.group_type,
            "habit": groupprofile.habit
        },
        "invite": {
            "code": invite.code
        }
    }

# 코드로 모임 참여하기
@router.post("/group/invite/{invite_code}")
def invited_group(
    invite_code: str,
    db: Session = Depends(get_db),
    current_user_id: int = CUI
):
    group_id = crud.get_group_id_by_code(db, invite_code)
    if not group_id:
        raise HTTPException(status_code=404, detail="초대코드가 잘못 되었거나 만료 되었습니다.")
    
    new_member, error = crud.join_group(db, group_id, current_user_id)
    if error:
        if error == "모임을 찾을 수 없습니다.":
            raise HTTPException(status_code=404, detail=error)
        elif error == "이미 모임에 가입 된 사용자입니다.":
            raise HTTPException(status_code=400, detail=error)
    
    return {"message": "초대코드로 그룹 가입", "group_id": new_member.group_id, "user_id": new_member.user_id}
# 모임 탈퇴하기

# ================13-1 모임 구해요=================

# 함께하기로 모임 참가
@router.post("/group/post/{post_id}")
def join_group(
    post_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = CUI
):
    group_id = crud.get_or_create_group_id_by_post(db, post_id, current_user_id)

    new_member, error = crud.join_group(db, group_id, current_user_id)
    if error:
        if error == "모임을 찾을 수 없습니다.":
            raise HTTPException(status_code=404, detail=error)
        elif error == "이미 모임에 가입 된 사용자입니다.":
            raise HTTPException(status_code=400, detail=error)
    
    return {"message": "초대코드로 그룹 가입", "group_id": new_member.group_id, "user_id": new_member.user_id}