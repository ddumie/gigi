# TODO: 비즈니스 로직 작성 (담당: 이영진)
# service.py
from backend.domains.neighbor.crud import (
   create_post, create_group_search_post,
   list_group_search,
   delete_group_search,
)
from sqlalchemy.orm import Session
from backend.domains.neighbor.schemas import GroupSearchCreate
from fastapi import HTTPException
from backend.domains.neighbor.schemas import PostAuthorResponse

def create_group_search(post: GroupSearchCreate, user_id: int, db: Session):
    # 비즈니스 규칙: 제목이 비어있으면 거절
    if not post.title or not post.title.strip():
        raise HTTPException(status_code=400, detail="제목을 입력해주세요.")

    # crud 1: 부모 Post 생성
    db_post = create_post(author_id=user_id, post_type="group_search", db=db)

    # crud 2: 자식 GroupSearchPost 생성
    create_group_search_post(post_id=db_post.id, post=post, db=db)

    return {"id": db_post.id, "message": "등록 완료"}

def list_group_search_logic(db: Session):
    result = []
    rows = list_group_search(db=db)
    for group_search, user in rows:
        group_search.author = PostAuthorResponse(id=user.id, nickname=user.nickname)
        result.append(group_search)
    
    return result

def delete_group_search_logic(post_id: int, user_id: int, db: Session):
    post = delete_group_search(post_id, user_id, db)
    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")
    post.is_active = False
    db.commit()