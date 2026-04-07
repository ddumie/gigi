from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func
from backend.database import Base


class Post(Base):
    """이웃 탭 게시글: 습관 공유 피드와 group-search를 함께 관리한다."""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    post_type = Column(String, nullable=False)           # "feed" / "group_search"

    category = Column(String, nullable=True)             # 운동, 식단, 복약, 수면, 기타
    content = Column(String, nullable=True)              # 습관 완료 후 한마디

    title = Column(String, nullable=True)                # group-search 제목
    description = Column(String, nullable=True)          # group-search 설명
    group_type = Column(String, nullable=True)           # family, friend, health_challenge, neighbors
    habit_title = Column(String, nullable=True)          # 함께할 습관 1개
    frequency = Column(String, nullable=True)            # 매일, 주3회 등

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PostSupport(Base):
    """게시글 지지 토글."""

    __tablename__ = "post_supports"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
