# TODO: 비즈니스 로직 작성 (담당: 이영진)
# service.py
from backend.domains.neighbor.crud import (
   create_post, create_group_search,
   get_group_search,
   delete_group_search,
   get_my_group_search,
   get_my_habits,
   get_habit, create_habit_feed,
   get_habit_feed,
   delete_habit_feed,
   get_feed_detail, get_feed_comments, get_post, create_feed_comment,
   delete_feed_comment,
   get_support,

)
from sqlalchemy.orm import Session
from backend.domains.neighbor.schemas import GroupSearchCreate, PostAuthorResponse
from fastapi import HTTPException
from backend.domains.neighbor.models import FeedPost, PostSupport

def create_group_search_logic(post: GroupSearchCreate, user_id: int, db: Session):
    # 비즈니스 규칙: 제목이 비어있으면 거절
    if not post.title or not post.title.strip():
        raise HTTPException(status_code=400, detail="제목을 입력해주세요.")

    # crud 1: 부모 Post 생성
    db_post = create_post(author_id=user_id, post_type="group_search", db=db)

    # crud 2: 자식 GroupSearchPost 생성
    create_group_search(post_id=db_post.id, post=post, db=db)

    return {"id": db_post.id, "message": "등록 완료"}

def get_group_search_logic(db: Session):
    result = []
    rows = get_group_search(db=db)
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
    return {"message": "삭제 완료"}

def get_my_group_search_logic(user_id: int, db: Session):
    result = []
    posts = get_my_group_search(user_id=user_id, db=db)
    for group_search, user in posts:
        group_search.author = PostAuthorResponse(id=user.id, nickname=user.nickname)
        result.append(group_search)

    return result

def get_my_habits_logic(user_id: int, db: Session):
    result = []
    posts = get_my_habits(user_id=user_id, db=db)
    for habits_feed, user in posts:
        habits_feed.author = PostAuthorResponse(id=user.id, nickname=user.nickname)
        result.append(habits_feed)
    return result

def create_habit_feed_logic(habit_id: int, content: str, user_id: int, db: Session) -> dict:
    habit = get_habit(habit_id=habit_id, user_id=user_id, db=db)
    if not habit:
        raise HTTPException(status_code=404, detail="습관을 찾을 수 없습니다.")
    return create_habit_feed(category=habit.category, content=content, user_id=user_id, db=db)

def get_habit_feed_logic(db: Session, category: str | None = None) -> list[FeedPost]:
    result = []
    rows = get_habit_feed(category=category, db=db)
    for feed, user in rows:
        feed.author = PostAuthorResponse(id=user.id, nickname=user.nickname)
        result.append(feed)
    return result

def delete_habit_feed_logic(post_id: int, user_id: int, db: Session):
    post = delete_habit_feed(post_id=post_id, user_id=user_id, db=db)
    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")
    post.is_active = False
    db.commit()
    return {"message": "삭제 완료"}

def get_feed_detail_logic(post_id: int, db: Session):
    row = get_feed_detail(post_id=post_id, db=db)
    if not row:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다.")
    feed, post, user = row
    feed.author = PostAuthorResponse(id=user.id, nickname=user.nickname)
    feed.created_at = post.created_at
    return feed

def get_feed_comments_logic(post_id: int, db: Session):
    rows = get_feed_comments(post_id=post_id, db=db)
    result = []
    for comment, user in rows:
        result.append({
            "id": comment.id,
            "post_id": comment.post_id,
            "author_id": comment.author_id,
            "author_nickname": user.nickname,
            "content": comment.content,
            "created_at": comment.created_at,
        })
    return result

def create_feed_comment_logic(post_id: int, content: str, user_id: int, db: Session):
    post = get_post(post_id=post_id, db=db)
    if not post:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다.")
    return create_feed_comment(post_id=post_id, content=content, user_id=user_id, db=db)

def delete_feed_comment_logic(comment_id: int, post_id: int, user_id: int, db: Session):
    comment = delete_feed_comment(comment_id=comment_id, post_id=post_id, user_id=user_id, db=db)
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    db.delete(comment)
    db.commit()
    return {"message": "댓글 삭제 완료"} 

def toggle_support_logic(post_id: int, user_id: int, db: Session):
    existing = get_support(post_id=post_id, user_id=user_id, db=db)
    if existing:
        db.delete(existing)
        db.commit()
        return {"supported": False}
    else:
        db.add(PostSupport(post_id=post_id, user_id=user_id))
        db.commit()
        return {"supported": True}    