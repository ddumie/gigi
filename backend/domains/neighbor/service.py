# TODO: 비즈니스 로직 작성 (담당: 이영진)
# service.py
from backend.domains.neighbor.crud import (
   create_post, create_group_search,
   get_group_search,
   update_group_search,
   delete_group_search,
   get_my_group_search,
   get_my_habits,
   get_habit, create_habit_feed,
   get_habit_feed,
   update_habit_feed,
   delete_habit_feed,
   get_feed_detail, get_feed_comments, get_post, create_feed_comment,
   update_feed_comment,
   delete_feed_comment,
   get_support,
   get_today_completion,

)
from sqlalchemy.ext.asyncio import AsyncSession
from backend.domains.neighbor.schemas import GroupSearchCreate, PostAuthorResponse
from fastapi import HTTPException
from backend.domains.neighbor.models import Comment, FeedPost, PostSupport, GroupSearchPost
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from backend.domains.habits.service import resolve_habit_meta
from backend.domains.support.models import Group


async def create_group_search_logic(post: GroupSearchCreate, user_id: int, db: AsyncSession):
    # 비즈니스 규칙: 제목이 비어있으면 거절
    if not post.title or not post.title.strip():
        raise HTTPException(status_code=400, detail="제목을 입력해주세요.")
    
    try:
        # crud 1: 부모 Post 생성
        db_post = await create_post(author_id=user_id, post_type="group_search", db=db)
        # crud 2: 자식 GroupSearchPost 생성
        await create_group_search(post_id=db_post.id, post=post, db=db)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="등록에 실패했습니다.")
    
    return {"id": db_post.id, "message": "등록 완료"}

async def get_group_search_logic(db: AsyncSession):
    result = []
    rows = await get_group_search(db=db)
    for group_search, post, user, member_count in rows:
        group_search.author = PostAuthorResponse(id=user.id, nickname=user.nickname)
        group_search.member_count = member_count
        group_search.updated_at = post.updated_at
        group_search.created_at = post.created_at
        result.append(group_search)
    
    return result

async def update_group_search_logic(post_id: int, user_id: int, post: GroupSearchCreate, db: AsyncSession):
    try:
        result = await update_group_search(post_id=post_id, user_id=user_id, post=post, db=db)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="수정에 실패하였습니다.")
    if not result:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")
    return {"message": "수정 완료"}

async def delete_group_search_logic(post_id: int, user_id: int, db: AsyncSession):
    post = await delete_group_search(post_id, user_id, db)
    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")
    try:
        # 1. GroupSearchPost 삭제
        r = await db.execute(select(GroupSearchPost).filter(GroupSearchPost.post_id == post_id))
        group_search = r.scalars().first()
        if group_search:
            await db.delete(group_search)

        # 2. groups.post_id → NULL (nullable 컬럼이므로 SET NULL)
        r = await db.execute(select(Group).filter(Group.post_id == post_id))
        for group in r.scalars().all():
            group.post_id = None

        # 3. 댓글 삭제
        r = await db.execute(select(Comment).filter(Comment.post_id == post_id))
        for comment in r.scalars().all():
            await db.delete(comment)

        # 4. 지지 삭제
        r = await db.execute(select(PostSupport).filter(PostSupport.post_id == post_id))
        for support in r.scalars().all():
            await db.delete(support)

        await db.delete(post)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="삭제에 실패하였습니다.")
    return {"message": "삭제 완료"}

async def get_my_group_search_logic(user_id: int, db: AsyncSession):
    result = []
    posts = await get_my_group_search(user_id=user_id, db=db)
    for group_search, post, user in posts:
        group_search.author = PostAuthorResponse(id=user.id, nickname=user.nickname)
        group_search.created_at = post.created_at
        result.append(group_search)

    return result

async def get_my_habits_logic(user_id: int, db: AsyncSession):
    result = []
    posts = await get_my_habits(user_id=user_id, db=db)
    for habits_feed, post, user in posts:
        habits_feed.author = PostAuthorResponse(id=user.id, nickname=user.nickname)
        habits_feed.created_at = post.created_at
        result.append(habits_feed)

    checked_count, total_count = await get_today_completion(user_id=user_id, db=db)
    today_all_done = total_count > 0 and checked_count >= total_count    
    return {"posts": result, "today_all_done": today_all_done}

async def create_habit_feed_logic(habit_id: int, content: str, user_id: int, db: AsyncSession) -> dict:
    habit = await get_habit(habit_id=habit_id, user_id=user_id, db=db)
    if not habit:
        raise HTTPException(status_code=404, detail="습관을 찾을 수 없습니다.")
    
    meta = await resolve_habit_meta(db, habit)
    try:
        result = await create_habit_feed(habit_id=habit_id, category=meta["category"], content=content, user_id=user_id, original_group_id=habit.group_id, db=db)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="피드 등록에 실패했습니다.")
    return result
    
async def get_habit_feed_logic(db: AsyncSession, category: str | None = None) -> list[FeedPost]:
    result = []
    rows = await get_habit_feed(category=category, db=db)
    for feed, post, user, habit, comment_count, group, member in rows:
        feed.author = PostAuthorResponse(id=user.id, nickname=user.nickname)
        feed.created_at = post.created_at
        feed.habit_title = habit.title if habit else None
        feed.habit_description = habit.description if habit else None
        feed.group_id = feed.original_group_id
        feed.group_name = group.name if group else None
        feed.is_member = member is not None
        feed.comment_count = comment_count
        result.append(feed)
    return result

async def update_habit_feed_logic(post_id: int, user_id: int, content: str, db: AsyncSession):
    try:
        result = await update_habit_feed(post_id=post_id, user_id=user_id, content=content, db=db)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="수정에 실패했습니다.")
    if not result:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다.")
    return {"message": "수정 완료"}

async def delete_habit_feed_logic(post_id: int, user_id: int, db: AsyncSession):
    post = await delete_habit_feed(post_id=post_id, user_id=user_id, db=db)
    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")
    try:
        await db.delete(post)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="삭제에 실패했습니다.")
    return {"message": "삭제 완료"}

async def get_feed_detail_logic(post_id: int, db: AsyncSession):
    row = await get_feed_detail(post_id=post_id, db=db)
    if not row:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다.")
    feed, post, user, habit = row
    feed.author = PostAuthorResponse(id=user.id, nickname=user.nickname)
    feed.created_at = post.created_at
    feed.habit_title = habit.title if habit else None           # 추가
    feed.habit_description = habit.description if habit else None  # 추가
    return feed

async def get_feed_comments_logic(post_id: int, db: AsyncSession):
    rows = await get_feed_comments(post_id=post_id, db=db)
    result = []
    for comment, user in rows:
        result.append({
            "id": comment.id,
            "post_id": comment.post_id,
            "author_id": comment.author_id,
            "author_nickname": user.nickname,
            "content": comment.content,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
        })
    return result

async def create_feed_comment_logic(post_id: int, content: str, user_id: int, db: AsyncSession):
    post = await get_post(post_id=post_id, db=db)
    if not post:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다.")
    try:
        return await create_feed_comment(post_id=post_id, content=content, user_id=user_id, db=db)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="댓글 등록에 실패했습니다.")

async def update_feed_comment_logic(comment_id: int, post_id: int, user_id: int, content: str, db: AsyncSession):
    try:
        comment = await update_feed_comment(comment_id=comment_id, post_id=post_id, user_id=user_id, content=content, db=db)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="댓글 수정에 실패했습니다.")
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    return {"message": "댓글 수정 완료"}

async def delete_feed_comment_logic(comment_id: int, post_id: int, user_id: int, db: AsyncSession):
    comment = await delete_feed_comment(comment_id=comment_id, post_id=post_id, user_id=user_id, db=db)
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    try:
        await db.delete(comment)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="댓글 삭제에 실패했습니다.")
    return {"message": "댓글 삭제 완료"} 

async def toggle_support_logic(post_id: int, user_id: int, db: AsyncSession):
    existing = await get_support(post_id=post_id, user_id=user_id, db=db)
    try:
        if existing:
            await db.delete(existing)
            await db.commit()
            return {"supported": False}
        else:
            db.add(PostSupport(post_id=post_id, user_id=user_id))
            await db.commit()
            return {"supported": True}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="요청에 실패했습니다.")   