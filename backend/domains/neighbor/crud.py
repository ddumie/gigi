# TODO: DB CRUD 작성 (담당: 이영진)
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.domains.neighbor.models import GroupSearchPost, Post, FeedPost
from backend.domains.neighbor.schemas import GroupSearchCreate
from backend.domains.habits.models import Habit
from backend.domains.auth.models import User


# 현재 로그인 사용자 기준이 아니라 author_id와 동일한 user.id를 1로 고정하였기 때문에,
# 추후 수정해야 함.

# 글쓰기 post
def create_group_search(post: GroupSearchCreate, db: Session = Depends(get_db)):
    # 1. 부모 Post 먼저 생성
    db_post = Post(
        author_id=1,  # auth가 아직 없어서 임시 테스트 값으로 1을 넣음. 실제론 현재 로그인 유저 id current_user.id로 교체
        post_type="group_search"
    )
    db.add(db_post)
    db.commit()  # ← post.id 확보
    db.refresh(db_post)

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
def list_group_search(db: Session = Depends(get_db)):
    posts = (
        db.query(GroupSearchPost)
        .join(Post, GroupSearchPost.post_id == Post.id)
        .filter(Post.is_active == True)
        .order_by(Post.created_at.desc())
        .all()
    )
    return posts

# 글 삭제 기능(docs용)
def delete_group_search(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id, Post.author_id == 1).first() # 나중에 author_id를 current_user.id 로 교체
    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")
    post.is_active = False
    db.commit()
    return {"message": "삭제 완료"}

# my posts 페이지에서 내가 쓴 글 보여주기(일단 group-search 부터)
def list_my_group_search(db: Session = Depends(get_db)): 
    posts = (
        db.query(GroupSearchPost)
        .join(Post, GroupSearchPost.post_id == Post.id)
        .filter(Post.is_active == True, Post.author_id == 1)  # 나중에 author_id를 current_user.id로 교체
        .order_by(Post.created_at.desc())
        .all()

    )
    return posts

#my posts 페이지에서 내가 쓴 습관도 보여주기
def list_my_feed(db: Session = Depends(get_db)): 
    posts = (
        db.query(FeedPost)
        .join(Post, FeedPost.post_id == Post.id)
        .filter(Post.is_active == True, Post.author_id == 1)  # 나중에 author_id를 current_user.id로 교체
        .order_by(Post.created_at.desc())
        .all()

    )
    return posts
# 피드 등록 ( 방법 2 - 프론트에서 habit_id + content 보냄) 추후 방법 1(습관 완료와 피드 등록이 항상 같이 일어나야 하려면 수정 필요)
def create_feed_post(habit_id: int, content: str = "", db: Session = Depends(get_db)):
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="습관을 찾을 수 없습니다.")

    db_post = Post(author_id=habit.user_id, post_type="feed")
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    db_feed = FeedPost(
        post_id=db_post.id,
        category=habit.category,
        content=content
    )
    db.add(db_feed)
    db.commit()
    return {"id": db_post.id, "message": "피드 등록 완료"}


# 피드 목록 조회 (category 파라미터로 필터)
def list_feed(category: str = None, db: Session = Depends(get_db)): # category = ("운동", "복약", "식단", "수면", "기타")
    query = (
        db.query(FeedPost)
        .join(Post, FeedPost.post_id == Post.id)
        .filter(Post.is_active == True)
        .order_by(Post.created_at.desc())
    )
    if category:
        query = query.filter(FeedPost.category == category)

    posts = query.all()
    return posts

# 피드 목록 지우기
def delete_feed(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id, Post.author_id == 1).first()  # 나중에 author_id를 current_user.id로 교체
    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")
    post.is_active = False
    db.commit()
    return {"message": "삭제 완료"}
