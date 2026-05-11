from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_async_db
from backend.domains.neighbor import service as neighbor_service
from backend.domains.neighbor.schemas import (
    GroupSearchCreate, GroupSearchResponse, 
    FeedPostResponse, HabitFeedCreate, HabitFeedUpdate,
    FeedDetailResponse, NeighborCommentCreate, NeighborCommentResponse,
    MyFeedResponse,    
)
from backend.domains.auth.router import get_current_user
from backend.domains.auth.models import User


router = APIRouter()



# 글쓰기 post
@router.post("/group-search")
async def create_group_search_final(post: GroupSearchCreate, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    return await neighbor_service.create_group_search_logic(post=post, user_id=current_user.id, db=db)

# 글쓰기 내용 읽어오기
@router.get("/group-search", response_model=list[GroupSearchResponse])
async def get_group_search_final(db: AsyncSession = Depends(get_async_db)):
    return await neighbor_service.get_group_search_logic(db=db)

# 글쓰기 수정
@router.put("/group-search/{post_id}")
async def update_group_search_final(post_id: int, post: GroupSearchCreate, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    return await neighbor_service.update_group_search_logic(post_id=post_id, user_id=current_user.id, post=post, db=db)

# 글 삭제 기능(docs용)
@router.delete("/group-search/{post_id}")
async def delete_group_search_final(post_id: int, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    return await neighbor_service.delete_group_search_logic(post_id=post_id, user_id=current_user.id, db=db)

# my posts 페이지에서 내가 쓴 글 보여주기(일단 group-search 부터)
@router.get("/group-search/my", response_model=list[GroupSearchResponse])
async def get_my_group_search_final(db: AsyncSession = Depends(get_async_db),  current_user: User = Depends(get_current_user)): 
    return await neighbor_service.get_my_group_search_logic(user_id=current_user.id, db=db)

# 모임 정보 단건 조회
@router.get("/group-search/{post_id}", response_model=GroupSearchResponse)
async def get_group_search_detail_final(post_id: int, db: AsyncSession = Depends(get_async_db)):
    return await neighbor_service.get_group_search_detail_logic(post_id=post_id, db=db)

#my posts 페이지에서 내가 쓴 습관도 보여주기
@router.get("/feed/my", response_model=MyFeedResponse)
async def get_my_habits_final(db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)): 
    return await neighbor_service.get_my_habits_logic(user_id=current_user.id, db=db)

# 피드 등록 ( 방법 2 - 프론트에서 habit_id + content 보냄)
# habit_id = 내가 habits_list에 등록한 id(등록할 때 지정한 category에 대응)
@router.post("/feed")
async def create_habit_feed_final(body: HabitFeedCreate, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    return await neighbor_service.create_habit_feed_logic(habit_id=body.habit_id, content=body.content, user_id=current_user.id, db=db)


# 피드 목록 조회 (category 파라미터로 필터)
# category 가 등록한 habit_id에 대응되는 category 문자열만 가능(운동, 복용, exercise 만 현재 가능)
@router.get("/feed", response_model=list[FeedPostResponse])
async def get_habit_feed_final(category: str = None, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)): # category = ("운동", "복약", "식단", "수면", "기타")
    return await neighbor_service.get_habit_feed_logic(db=db, category=category, user_id=current_user.id)

# 습관 피드 수정
@router.put("/feed/{post_id}")
async def update_habit_feed_final(post_id: int, body: HabitFeedUpdate, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    return await neighbor_service.update_habit_feed_logic(post_id=post_id, user_id=current_user.id, content=body.content, db=db)

# 피드 목록 지우기
@router.delete("/feed/{post_id}")
async def delete_habit_feed_final(post_id: int, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    return await neighbor_service.delete_habit_feed_logic(post_id=post_id, user_id=current_user.id, db=db)


# 피드 단건 조회
@router.get("/feed/{post_id}", response_model=FeedDetailResponse)
async def get_feed_detail_final(post_id: int, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    return await neighbor_service.get_feed_detail_logic(post_id=post_id, user_id=current_user.id, db=db)

# 댓글 목록 조회
@router.get("/feed/{post_id}/comments", response_model=list[NeighborCommentResponse])
async def get_feed_comments_final(post_id: int, db: AsyncSession = Depends(get_async_db)):
    return await neighbor_service.get_feed_comments_logic(post_id=post_id, db=db)

# 댓글 작성
@router.post("/feed/{post_id}/comments")
async def create_feed_comment_final(
    post_id: int,
    body: NeighborCommentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    return await neighbor_service.create_feed_comment_logic(post_id=post_id, content=body.content, user_id=current_user.id, db=db)

# 댓글 수정
@router.put("/feed/{post_id}/comments/{comment_id}")
async def update_feed_comment_final(
    post_id: int,
    comment_id: int,
    body: NeighborCommentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    return await neighbor_service.update_feed_comment_logic(comment_id=comment_id, post_id=post_id, user_id=current_user.id, content=body.content, db=db)

# 댓글 삭제
@router.delete("/feed/{post_id}/comments/{comment_id}")
async def delete_feed_comment_final(
    post_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    return await neighbor_service.delete_feed_comment_logic(comment_id=comment_id, post_id=post_id, user_id=current_user.id, db=db)

# 지지하기 토글
@router.post("/feed/{post_id}/support")
async def support_toggle_final(
    post_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    return await neighbor_service.toggle_support_logic(post_id=post_id, user_id=current_user.id, db=db)

# 지지 횟수 조회
@router.get("/feed/{post_id}/support")
async def feed_support_info(
    post_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    return await neighbor_service.get_support_info_logic(post_id=post_id, user_id=current_user.id, db=db)