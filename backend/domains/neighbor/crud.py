# TODO: DB CRUD 작성 (담당: 이영진)
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.domains.neighbor.models import GroupSearchPost, Post, FeedPost, Comment, PostSupport
from backend.domains.neighbor.schemas import GroupSearchCreate
from backend.domains.habits.models import Habit
from backend.domains.auth.models import User
from backend.domains.support.models import Group, GroupMember


# 현재 로그인 사용자 기준이 아니라 author_id와 동일한 user.id를 1로 고정하였기 때문에,
# 추후 수정해야 함.
# 글쓰기 post
async def create_post(author_id: int, post_type: str, db: AsyncSession) -> Post:
    # 1. 부모 Post 먼저 생성
    db_post = Post(
        author_id=author_id,  # auth가 아직 없어서 임시 테스트 값으로 1을 넣음. 실제론 현재 로그인 유저 id current_user.id로 교체
        post_type=post_type
    )
    db.add(db_post)
    await db.commit()  # ← post.id 확보
    await db.refresh(db_post)
    return db_post # ← 결과를 반환만 함, 판단은 안 함

async def create_group_search(post_id: int, post: GroupSearchCreate, db: AsyncSession) -> GroupSearchPost:
   # 2. 자식 GroupSearchPost 생성
    db_group_search = GroupSearchPost(
        post_id=post_id,
        title=post.title,
        description=post.description,
        group_type=post.group_type,
        habit_title=post.habit_title,
        frequency=post.frequency,
        category=post.category
    )
    db.add(db_group_search)
    await db.commit()
    await db.refresh(db_group_search)
    return db_group_search

# 글쓰기 내용 읽어오기
async def get_group_search(db: AsyncSession) -> list[tuple[GroupSearchPost, User]]:
    result = await db.execute(
        select(GroupSearchPost, Post, User, func.count(GroupMember.id).label('member_count'))
        .join(Post, GroupSearchPost.post_id == Post.id)
        .join(User, Post.author_id == User.id)
        .outerjoin(Group, Group.post_id == Post.id)
        .outerjoin(GroupMember, GroupMember.group_id == Group.id)
        .filter(Post.is_active == True)
        .group_by(GroupSearchPost.id, Post.id, User.id)
        .order_by(Post.created_at.desc())
    )
    return result.all()

#
async def update_group_search(post_id: int, user_id: int, post: GroupSearchCreate, db: AsyncSession) -> GroupSearchPost | None:
    result = await db.execute(select(Post).filter(Post.id == post_id, Post.author_id == user_id))
    db_post = result.scalars().first()
    if not db_post:
        return None
    results = await db.execute(select(GroupSearchPost).filter(GroupSearchPost.post_id == post_id))
    db_group_search = results.scalars().first()
    if not db_group_search:
        return None
    db_group_search.title = post.title
    db_group_search.description = post.description
    db_group_search.group_type = post.group_type
    db_group_search.habit_title = post.habit_title
    db_group_search.frequency = post.frequency
    db_group_search.category = post.category
    db_post.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(db_group_search)
    return db_group_search
 
# 글 삭제 기능(docs용)
async def delete_group_search(post_id: int, user_id: int, db: AsyncSession) -> Post | None:
    result = await db.execute(select(Post).filter(Post.id == post_id, Post.author_id == user_id))
    post = result.scalars().first() # 나중에 author_id를 current_user.id 로 교체
    return post

# my posts 페이지에서 내가 쓴 글 보여주기(일단 group-search 부터)
async def get_my_group_search(user_id: int, db: AsyncSession) -> list[tuple[GroupSearchPost, User]]: 
    result = await db.execute(
        select(GroupSearchPost, User)
        .join(Post, GroupSearchPost.post_id == Post.id)
        .join(User, Post.author_id == User.id)
        .filter(Post.is_active == True, Post.author_id == user_id)  # 나중에 author_id를 current_user.id로 교체
        .order_by(Post.created_at.desc())
    )
    return result.all()
    

#my posts 페이지에서 내가 쓴 습관도 보여주기
async def get_my_habits(user_id: int, db: AsyncSession) -> list[tuple[FeedPost, User]]: 
    result = await db.execute(
        select(FeedPost, User)
        .join(Post, FeedPost.post_id == Post.id)
        .join(User, Post.author_id == User.id)
        .filter(Post.is_active == True, Post.author_id == user_id)  # 나중에 author_id를 current_user.id로 교체
        .order_by(Post.created_at.desc())
    )

    return result.all()


# 습관 조회
async def get_habit(habit_id: int, user_id: int, db: AsyncSession) -> Habit | None:
    result = await db.execute(select(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id))
    return result.scalars().first()

# 피드 등록 
async def create_habit_feed(habit_id: int, category: str, content: str, user_id: int, db: AsyncSession) -> dict:
    db_post = Post(author_id=user_id, post_type="feed")
    db.add(db_post)
    await db.commit()
    await db.refresh(db_post)
    
    db_feed = FeedPost(
        post_id=db_post.id,
        habit_id=habit_id,
        category=category,
        content=content
    )
    db.add(db_feed)
    await db.commit()
        
    return {"id": db_post.id, "message": "피드 등록 완료"}


# 피드 목록 조회 (category 파라미터로 필터)
async def get_habit_feed(db: AsyncSession, category: str | None = None) -> list[FeedPost, User]: # category = ("운동", "복약", "식단", "수면", "기타")
    stmt = (
        select(FeedPost, Post, User, Habit, func.count(Comment.id).label("comment_count"))
        .join(Post, FeedPost.post_id == Post.id)
        .join(User, Post.author_id == User.id)
        .outerjoin(Habit, FeedPost.habit_id == Habit.id)
        .outerjoin(Comment, Comment.post_id == Post.id)
        .filter(Post.is_active == True)
        .group_by(FeedPost.id, Post.id, User.id, Habit.id)
        .order_by(Post.created_at.desc())
    )
    if category:
        stmt = stmt.filter(FeedPost.category == category)
    result = await db.execute(stmt)
    return result.all()

# 습관피드 업데이트
async def update_habit_feed(post_id: int, user_id: int, content: str, db: AsyncSession) -> FeedPost | None:
    result = await db.execute(select(Post).filter(Post.id == post_id, Post.author_id == user_id))
    db_post = result.scalars().first()
    if not db_post:
        return None
    results = await db.execute(select(FeedPost).filter(FeedPost.post_id == post_id))
    db_feed = results.scalars().first()
    if not db_feed:
        return None
    db_feed.content = content
    await db.commit()
    await db.refresh(db_feed)
    return db_feed
    

# 피드 목록 지우기
async def delete_habit_feed(post_id: int, user_id: int, db: AsyncSession) -> Post | None:
    result = await db.execute(select(Post).filter(Post.id == post_id, Post.author_id == user_id))  # 나중에 author_id를 current_user.id로 교체
    post = result.scalars().first()
    return post

# 피드 단건 조회
async def get_feed_detail(post_id: int, db: AsyncSession) -> tuple[FeedPost, Post, User] | None:
    result = await db.execute(
        select(FeedPost, Post, User, Habit)
        .join(Post, FeedPost.post_id == Post.id)
        .join(User, Post.author_id == User.id)
        .outerjoin(Habit, FeedPost.habit_id == Habit.id)
        .filter(FeedPost.post_id == post_id, Post.is_active == True)
    )
    return result.first()

# 댓글 목록 조회
async def get_feed_comments(post_id: int, db: AsyncSession) -> list[tuple[Comment, User]]:
    result = await db.execute(
        select(Comment, User)
        .join(User, Comment.author_id == User.id)
        .filter(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
    )
    return result.all()

# 댓글 작성
async def get_post(post_id: int, db: AsyncSession) -> Post | None:
    result = await db.execute(select(Post).filter(Post.id == post_id, Post.is_active == True))
    return result.scalars().first()

async def create_feed_comment(post_id: int, content: str, user_id: int, db: AsyncSession) -> dict[str, int | str]:
    comment = Comment(post_id=post_id, author_id=user_id, content=content)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return {"id": comment.id, "message": "댓글 등록 완료"}
    
# 댓글 수정
async def update_feed_comment(comment_id: int, post_id: int, user_id: int, content: str, db: AsyncSession) -> Comment | None:
    result = await db.execute(
        select(Comment).filter(
            Comment.id == comment_id,
            Comment.post_id == post_id,
            Comment.author_id == user_id
        )
    )
    comment = result.scalars().first()
    if not comment:
        return None
    comment.content = content
    await db.commit()
    await db.refresh(comment)
    return comment

# 댓글 삭제
async def delete_feed_comment(comment_id: int, post_id: int, user_id: int, db: AsyncSession) -> Comment | None:
    result = await db.execute(
        select(Comment).filter(
            Comment.id == comment_id,
            Comment.post_id == post_id,   # ← post 소속 확인까지
            Comment.author_id == user_id
        )
    )
    return result.scalars().first()

# 지지하기 토글 (누르면 추가, 다시 누르면 취소)
async def get_support(post_id: int, user_id: int, db: AsyncSession) -> PostSupport | None:
    result = await db.execute(
        select(PostSupport).filter(
        PostSupport.post_id == post_id,
        PostSupport.user_id == user_id)
    )
    return result.scalars().first()
    
# 지지 횟수 + 내가 눌렀는지 조회
async def get_support_info(post_id: int, user_id: int, db: AsyncSession) -> dict[str, int]:
    count_result = await db.execute(
        select(func.count()).select_from(PostSupport).filter(PostSupport.post_id == post_id)
        )
    support_result = await db.execute(
        select(PostSupport).filter(PostSupport.post_id == post_id, 
                                   PostSupport.user_id == user_id)
    )
    return {"support_count": count_result.scalar(),
            "is_supported": support_result.scalars().first() is not None,
            }
