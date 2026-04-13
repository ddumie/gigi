from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.domains.neighbor.schemas import GroupSearchCreate, GroupSearchResponse,FeedPostResponse
from backend.domains.neighbor.crud import (
    create_group_search,
    list_group_search,
    delete_group_search,
    list_my_group_search,
    list_my_feed,
    create_feed_post,
    list_feed,
    delete_feed
)

router = APIRouter()

# 현재 로그인 사용자 기준이 아니라 author_id와 동일한 user.id를 1로 고정하였기 때문에,
# 추후 수정해야 함.


# 글쓰기 post
@router.post("/group-search")
def create_group_search_post(post: GroupSearchCreate, db: Session = Depends(get_db)):
    return create_group_search(post, db)

# 글쓰기 내용 읽어오기
@router.get("/group-search", response_model=list[GroupSearchResponse])
def list_group_search_get(db: Session = Depends(get_db)):
    return list_group_search(db)

# 글 삭제 기능(docs용)
@router.delete("/group-search/{post_id}")
def group_search_del(post_id: int, db: Session = Depends(get_db)):
    return delete_group_search(post_id, db)

# my posts 페이지에서 내가 쓴 글 보여주기(일단 group-search 부터)
@router.get("/group-search/my", response_model=list[GroupSearchResponse])
def list_my_group_search_get(db: Session = Depends(get_db)): 
    return list_my_group_search(db)

#my posts 페이지에서 내가 쓴 습관도 보여주기
@router.get("/feed/my", response_model=list[FeedPostResponse])
def list_my_feed_get(db: Session = Depends(get_db)): 
    return list_my_feed(db)

# 피드 등록 ( 방법 2 - 프론트에서 habit_id + content 보냄) 추후 방법 1(습관 완료와 피드 등록이 항상 같이 일어나야 하려면 수정 필요)
# habit_id = 내가 habits_list에 등록한 id(등록할 때 지정한 category에 대응)
@router.post("/feed")
def create_feed_create(habit_id: int, content: str = "", db: Session = Depends(get_db)):
    return create_feed_post(habit_id, content, db)


# 피드 목록 조회 (category 파라미터로 필터)
# category 가 등록한 habit_id에 대응되는 category 문자열만 가능(운동, 복용, exercise 만 현재 가능)
@router.get("/feed", response_model=list[FeedPostResponse])
def list_feed_get(category: str = None, db: Session = Depends(get_db)): # category = ("운동", "복약", "식단", "수면", "기타")
    return list_feed(category, db)


# 피드 목록 지우기
@router.delete("/feed/{post_id}")
def feed_del(post_id: int, db: Session = Depends(get_db)):
    return delete_feed(post_id, db)
