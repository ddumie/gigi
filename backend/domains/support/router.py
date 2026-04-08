from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import crud, schemas, service, models
from backend.database import get_db

router = APIRouter(prefix = "/support")

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

# 모임 참가



# 모임 생성
@router.post("/group_create")
def create_group(
    group: schemas.GroupCreate,
    db: Session = Depends(get_db),
    current_user_id: int = CUI
):
    db_group = crud.create_group(db, group, user_id = current_user_id)
    return {"group" : {"id": db_group.id}}

# =============== 12-2 모임 관리 ====================

# 모임 관리 읽어오기 (모임명, 모임 종류, 초대코드)
@router.get("/group_setting/{group_id}")
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
@router.post("group_participate/{group_id}")
def group_participate(
    group_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = CUI
)

# 모임 탈퇴하기