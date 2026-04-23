from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.database import Base


class Post(Base):
    """공통 필드만 담는 부모 테이블"""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    post_type = Column(String, nullable=False)  # "feed" / "group_search"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    feed = relationship("FeedPost", back_populates="post", uselist=False)
    group_search = relationship("GroupSearchPost", back_populates="post", uselist=False)


class FeedPost(Base):
    """습관 공유 피드 전용 필드"""
    __tablename__ = "feed_posts"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, unique=True)
    habit_id = Column(Integer, ForeignKey("habits_list.id"), nullable=True)
    category = Column(String, nullable=False)  # 운동, 식단, 복약, 수면, 기타
    content = Column(String, nullable=True)    # 습관 완료 후 한마디

    post = relationship("Post", back_populates="feed")


class GroupSearchPost(Base):
    """그룹 모집 게시글 전용 필드"""
    __tablename__ = "group_search_posts"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, unique=True)

    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    group_type = Column(String, nullable=False)   # family, friend, health_challenge, neighbors
    habit_title = Column(String, nullable=False)  # 함께할 습관
    frequency = Column(String, nullable=False)    # 매일, 주3회 등
    category = Column(String, nullable=True)

    post = relationship("Post", back_populates="group_search")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PostSupport(Base):
    """게시글 지지 토글."""

    __tablename__ = "post_supports"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
