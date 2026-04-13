from typing import Optional
from pydantic import BaseModel
from datetime import datetime

# 게시글 중 습관 피드 작성 내용
class FeedPostResponse(BaseModel):
    post_id: int # id 대신 post_id로
    category: Optional[str] = None
    content: str | None = None

    class Config:
        from_attributes = True
    

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

class GroupSearchResponse(BaseModel):
    id: int
    post_id: int
    title: str
    description: str
    group_type: str
    habit_title: str
    frequency: str

    class Config:
        from_attributes = True  # ORM 객체 → Pydantic 자동 변환

# 게시글 목록 / 상세 응답
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

# 댓글 작성 요청
class CommentCreate(BaseModel):
    content : str
    parent_id : int

# 댓글 응답
class CommentResponse(BaseModel):
    id : int
    content : str
    is_soft_deleted : bool 
    author_id : int 
    post_id : int 
    parent_id : int 
    created_at : datetime

# 좋아요
class support(BaseModel):
    id : int
    user_id : int
    post_id : int
    created_at : datetime

