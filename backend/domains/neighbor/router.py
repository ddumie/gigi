from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.domains.neighbor.service import (
    create_group_search,
    list_group_search_logic,
    delete_group_search_logic,
    list_my_group_search_logic,
    list_my_feed_logic,
    create_feed_post_logic,
    list_feed_logic,
    delete_feed_logic,
    get_feed_detail_logic,get_feed_comments_logic, create_feed_comment_logic,
    delete_feed_comment_logic,
    toggle_support_logic,

)
from backend.domains.neighbor.schemas import (
    GroupSearchCreate, GroupSearchResponse, FeedPostResponse,
    FeedDetailResponse, NeighborCommentCreate, NeighborCommentResponse
)
from backend.domains.auth.router import get_current_user
from backend.domains.auth.models import User
from backend.domains.neighbor.crud import (
    
    

    
    get_support_info
)

router = APIRouter()

# 현재 로그인 사용자 기준이 아니라 author_id와 동일한 user.id를 1로 고정하였기 때문에,
# 추후 수정해야 함.


# 글쓰기 post
@router.post("/group-search")
def post_group_search(post: GroupSearchCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_group_search(post=post, user_id=current_user.id, db=db)

# 글쓰기 내용 읽어오기
@router.get("/group-search", response_model=list[GroupSearchResponse])
def list_group_search_get(db: Session = Depends(get_db)):
    return list_group_search_logic(db=db)

# 글 삭제 기능(docs용)
@router.delete("/group-search/{post_id}")
def group_search_del(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return delete_group_search_logic(post_id=post_id, user_id=current_user.id, db=db)

# my posts 페이지에서 내가 쓴 글 보여주기(일단 group-search 부터)
@router.get("/group-search/my", response_model=list[GroupSearchResponse])
def list_my_group_search_get(db: Session = Depends(get_db),  current_user: User = Depends(get_current_user)): 
    return list_my_group_search_logic(user_id=current_user.id, db=db)

#my posts 페이지에서 내가 쓴 습관도 보여주기
@router.get("/feed/my", response_model=list[FeedPostResponse])
def list_my_feed_get(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): 
    return list_my_feed_logic(user_id=current_user.id, db=db)

# 피드 등록 ( 방법 2 - 프론트에서 habit_id + content 보냄) 추후 방법 1(습관 완료와 피드 등록이 항상 같이 일어나야 하려면 수정 필요)
# habit_id = 내가 habits_list에 등록한 id(등록할 때 지정한 category에 대응)
@router.post("/feed")
def create_feed_create(habit_id: int, content: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_feed_post_logic(habit_id=habit_id, content=content, user_id=current_user.id, db=db)


# 피드 목록 조회 (category 파라미터로 필터)
# category 가 등록한 habit_id에 대응되는 category 문자열만 가능(운동, 복용, exercise 만 현재 가능)
@router.get("/feed", response_model=list[FeedPostResponse])
def list_feed_get(category: str = None, db: Session = Depends(get_db)): # category = ("운동", "복약", "식단", "수면", "기타")
    return list_feed_logic(db=db, category=category)


# 피드 목록 지우기
@router.delete("/feed/{post_id}")
def feed_del(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return delete_feed_logic(post_id=post_id, user_id=current_user.id, db=db)


# 피드 단건 조회
@router.get("/feed/{post_id}", response_model=FeedDetailResponse)
def feed_detail(post_id: int, db: Session = Depends(get_db)):
    return get_feed_detail_logic(post_id=post_id, db=db)

# 댓글 목록 조회
@router.get("/feed/{post_id}/comments", response_model=list[NeighborCommentResponse])
def feed_comments(post_id: int, db: Session = Depends(get_db)):
    return get_feed_comments_logic(post_id=post_id, db=db)

# 댓글 작성
@router.post("/feed/{post_id}/comments")
def feed_comment_create(
    post_id: int,
    body: NeighborCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_feed_comment_logic(post_id=post_id, content=body.content, user_id=current_user.id, db=db)

# 댓글 삭제
@router.delete("/feed/{post_id}/comments/{comment_id}")
def feed_comment_delete(
    post_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return delete_feed_comment_logic(comment_id=comment_id, post_id=post_id, user_id=current_user.id, db=db)

# 지지하기 토글
@router.post("/feed/{post_id}/support")
def feed_support_toggle(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return toggle_support_logic(post_id=post_id, user_id=current_user.id, db=db)

# 지지 횟수 조회
@router.get("/feed/{post_id}/support")
def feed_support_info(
    post_id: int,
    db: Session = Depends(get_db),
):
    return get_support_info(post_id=post_id, db=db)