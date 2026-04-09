from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db
from backend.domains.neighbor.models import GroupSearchPost, Post

router = APIRouter()

# TODO: 엔드포인트 작성 (담당: 이영진)

class GroupSearchCreate(BaseModel):
    title: str
    description: str
    group_type: str
    habit_title: str
    frequency: str

# 글쓰기 post
@router.post("/group-search")
def create_group_search(post: GroupSearchCreate, db: Session = Depends(get_db)):
    # 1. 부모 Post 먼저 생성
    db_post = Post(
        author_id=1,  # 실제론 현재 로그인 유저 id current_user.id로 교체
        post_type="group_search"
    )
    db.add(db_post)
    db.commit()  # ← post.id 확보
    db.refresh(db_post)


    print(db_post.id)
   # 2. 자식 GroupSearchPost 생성
    db_group_search = GroupSearchPost(
        post_id=db_post.id,
        title=post.title,
        description=post.description,
        group_type=post.group_type,
        habit_title=post.habit_title,
        frequency=post.frequency,
    )
    db.add(db_group_search)
    db.commit()
    db.refresh(db_post)
    return {"id": db_post.id, "message": "등록 완료"}

# 글쓰기 내용 읽어오기
@router.get("/group-search")
def list_group_search(db: Session = Depends(get_db)):
    posts = (
        db.query(GroupSearchPost)
        .join(Post, GroupSearchPost.post_id == Post.id)
        .filter(Post.is_active == True)
        .order_by(Post.created_at.desc())
        .all()
    )
    return [
        {
            "id": p.post_id,
            "title": p.title,
            "description": p.description,
            "group_type": p.group_type,
            "habit_title": p.habit_title,
            "frequency": p.frequency,
        }
        for p in posts
    ]
# 글 삭제 기능(docs용)
@router.delete("/group-search/{post_id}")
def delete_group_search(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id, Post.author_id == 1).first()
    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")
    post.is_active = False
    db.commit()
    return {"message": "삭제 완료"}

# my posts 페이지에서 내가 쓴 글 보여주기(일단 group-search 부터)
@router.get("/group-search/my")
def list_my_group_search(db: Session = Depends(get_db)):
    posts = (
        db.query(GroupSearchPost)
        .join(Post, GroupSearchPost.post_id == Post.id)
        .filter(Post.is_active == True, Post.author_id == 1)  # 나중에 current_user.id로 교체
        .order_by(Post.created_at.desc())
        .all()
    )
    return [
        {
            "id": p.post_id,
            "title": p.title,
            "description": p.description,
            "group_type": p.group_type,
            "habit_title": p.habit_title,
            "frequency": p.frequency,
        }
        for p in posts
    ]
