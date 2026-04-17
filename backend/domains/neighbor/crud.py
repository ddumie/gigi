# TODO: DB CRUD 작성 (담당: 이영진)
from sqlalchemy.orm import Session
from backend.domains.neighbor.models import GroupSearchPost, Post, FeedPost, Comment, PostSupport
from backend.domains.neighbor.schemas import GroupSearchCreate
from backend.domains.habits.models import Habit
from backend.domains.auth.models import User


# 현재 로그인 사용자 기준이 아니라 author_id와 동일한 user.id를 1로 고정하였기 때문에,
# 추후 수정해야 함.
# 글쓰기 post
def create_post(author_id: int, post_type: str, db: Session) -> Post:
    # 1. 부모 Post 먼저 생성
    db_post = Post(
        author_id=author_id,  # auth가 아직 없어서 임시 테스트 값으로 1을 넣음. 실제론 현재 로그인 유저 id current_user.id로 교체
        post_type=post_type
    )
    db.add(db_post)
    db.commit()  # ← post.id 확보
    db.refresh(db_post)
    return db_post # ← 결과를 반환만 함, 판단은 안 함

def create_group_search(post_id: int, post: GroupSearchCreate, db: Session) -> GroupSearchPost:
   # 2. 자식 GroupSearchPost 생성
    db_group_search = GroupSearchPost(
        post_id=post_id,
        title=post.title,
        description=post.description,
        group_type=post.group_type,
        habit_title=post.habit_title,
        frequency=post.frequency,
    )
    db.add(db_group_search)
    db.commit()
    db.refresh(db_group_search)
    return db_group_search

# 글쓰기 내용 읽어오기
def list_group_search(db: Session) -> list[tuple[GroupSearchPost, User]]:
    rows = (
        db.query(GroupSearchPost, User)
        .join(Post, GroupSearchPost.post_id == Post.id)
        .join(User, Post.author_id == User.id)
        .filter(Post.is_active == True)
        .order_by(Post.created_at.desc())
        .all()
    )
    return rows

# 글 삭제 기능(docs용)
def delete_group_search(post_id: int, user_id: int, db: Session) -> Post | None:
    post = db.query(Post).filter(Post.id == post_id, Post.author_id == user_id).first() # 나중에 author_id를 current_user.id 로 교체
    return post

# my posts 페이지에서 내가 쓴 글 보여주기(일단 group-search 부터)
def list_my_group_search(user_id: int, db: Session) -> list[tuple[GroupSearchPost, User]]: 
    posts = (
        db.query(GroupSearchPost, User)
        .join(Post, GroupSearchPost.post_id == Post.id)
        .join(User, Post.author_id == User.id)
        .filter(Post.is_active == True, Post.author_id == user_id)  # 나중에 author_id를 current_user.id로 교체
        .order_by(Post.created_at.desc())
        .all()
    )
    return posts
    

#my posts 페이지에서 내가 쓴 습관도 보여주기
def list_my_feed(user_id: int, db: Session) -> list[tuple[FeedPost, User]]: 
    posts = (
        db.query(FeedPost, User)
        .join(Post, FeedPost.post_id == Post.id)
        .join(User, Post.author_id == User.id)
        .filter(Post.is_active == True, Post.author_id == user_id)  # 나중에 author_id를 current_user.id로 교체
        .order_by(Post.created_at.desc())
        .all()

    )

    return posts


# 습관 조회
def get_habit(habit_id: int, user_id: int, db: Session) -> Habit | None:
    return db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()

# 피드 등록 ( 방법 2 - 프론트에서 habit_id + content 보냄) 추후 방법 1(습관 완료와 피드 등록이 항상 같이 일어나야 하려면 수정 필요)
def create_feed_post(category: str, content: str, user_id: int, db: Session) -> dict:
    db_post = Post(author_id=user_id, post_type="feed")
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    db_feed = FeedPost(
        post_id=db_post.id,
        category=category,
        content=content
    )
    db.add(db_feed)
    db.commit()
    return {"id": db_post.id, "message": "피드 등록 완료"}


# 피드 목록 조회 (category 파라미터로 필터)
def list_feed(db: Session, category: str | None = None) -> list[FeedPost, User]: # category = ("운동", "복약", "식단", "수면", "기타")
    query = (
        db.query(FeedPost, User)
        .join(Post, FeedPost.post_id == Post.id)
        .join(User, Post.author_id == User.id)
        .filter(Post.is_active == True)
        .order_by(Post.created_at.desc())
    )
    if category:
        query = query.filter(FeedPost.category == category)
    return query.all()

# 피드 목록 지우기
def delete_feed(post_id: int, user_id: int, db: Session) -> Post | None:
    post = db.query(Post).filter(Post.id == post_id, Post.author_id == user_id).first()  # 나중에 author_id를 current_user.id로 교체
    return post

# 피드 단건 조회
def get_feed_detail(post_id: int, db: Session) -> tuple[FeedPost, Post, User] | None:
    row = (
        db.query(FeedPost, Post, User)
        .join(Post, FeedPost.post_id == Post.id)
        .join(User, Post.author_id == User.id)
        .filter(FeedPost.post_id == post_id, Post.is_active == True)
        .first()
    )
    return row

# 댓글 목록 조회
def get_feed_comments(post_id: int, db: Session) -> list[tuple[Comment, User]]:
    rows = (
        db.query(Comment, User)
        .join(User, Comment.author_id == User.id)
        .filter(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    return rows

# 댓글 작성
def get_post(post_id: int, db: Session) -> Post | None:
    return db.query(Post).filter(Post.id == post_id, Post.is_active == True).first()

def create_feed_comment(post_id: int, content: str, user_id: int, db: Session) -> dict[str, int | str]:
    comment = Comment(post_id=post_id, author_id=user_id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {"id": comment.id, "message": "댓글 등록 완료"}

# 댓글 삭제
def delete_feed_comment(comment_id: int, post_id: int, user_id: int, db: Session) -> Comment | None:
    return db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.post_id == post_id,   # ← post 소속 확인까지
        Comment.author_id == user_id
    ).first()

# 지지하기 토글 (누르면 추가, 다시 누르면 취소)
def get_support(post_id: int, user_id: int, db: Session) -> PostSupport | None:
    return db.query(PostSupport).filter(
        PostSupport.post_id == post_id,
        PostSupport.user_id == user_id
    ).first()
    
# 지지 횟수 + 내가 눌렀는지 조회
def get_support_info(post_id: int, db: Session) -> dict[str, int]:
    count = db.query(PostSupport).filter(PostSupport.post_id == post_id).count()
    return {"support_count": count}
