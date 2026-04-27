from typing import Optional
from pydantic import BaseModel
from datetime import datetime


# 게시글 내 작성자 정보
class PostAuthorResponse(BaseModel):
    id: int
    nickname : Optional[str] = None

# 게시글 내용
class GroupSearchCreate(BaseModel):
    title: str
    description: str
    group_type: str
    habit_title: str
    frequency: str
    category: Optional[str] = None

class GroupSearchResponse(BaseModel):
    id: int
    post_id: int
    title: str
    description: str
    group_type: str
    habit_title: str
    frequency: str
    category: Optional[str] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    author: PostAuthorResponse
    member_count: int = 0

    class Config:
        from_attributes = True  # ORM 객체 → Pydantic 자동 변환


# 게시글 중 습관 피드 작성 내용
class FeedPostResponse(BaseModel):
    post_id: int # id 대신 post_id로
    category: Optional[str] = None
    content: str | None = None
    habit_title: Optional[str] = None
    habit_description: Optional[str] = None
    author: Optional[PostAuthorResponse] = None
    created_at: Optional[datetime] = None
    comment_count: int = 0

    class Config:
        from_attributes = True
# 습관 피드 생성
class HabitFeedCreate(BaseModel):
    habit_id: int
    content: str = ""

# 습관피드 업데이트
class HabitFeedUpdate(BaseModel):
    content: str


# 피드 상세 응답
class FeedDetailResponse(BaseModel):
    post_id: int
    category: Optional[str] = None
    content: Optional[str] = None
    habit_title: Optional[str] = None
    habit_description: Optional[str] = None
    author: Optional[PostAuthorResponse] = None
    created_at: Optional[datetime] = None
    support_count: int = 0
    is_supported: bool = False

    class Config:
        from_attributes = True

# 이웃 댓글 작성 요청
class NeighborCommentCreate(BaseModel):
    content: str

# 이웃 댓글 응답
class NeighborCommentResponse(BaseModel):
    id: int
    post_id: int
    author_id: int
    author_nickname: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
# =============================================================================
# 게시글 목록 / 상세 응답 (안 쓰는 스키마)
class PostListResponse(BaseModel):
    id : int
    title : str 
    content : str 
    view_count : Optional[int] = 0
    support_count : Optional[int] = 0
    comment_count : Optional[int] = 0
    is_soft_deleted : bool
    author : PostAuthorResponse
    category_id : int
    content_finished_at : datetime
    created_at : datetime
    updated_at : Optional[datetime] = None
    is_finished : bool

