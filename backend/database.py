from importlib import import_module

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings


MODEL_MODULES = (
    "backend.domains.auth.models",
    "backend.domains.onboarding.models",
    "backend.domains.habits.models",
    "backend.domains.support.models",
    "backend.domains.neighbor.models",
)

# 동기 엔진 - auth 도메인 비동기 전환 완료 시 삭제
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    async_database_url = settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)
else:
    engine = create_engine(settings.DATABASE_URL)
    async_database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# 비동기 엔진
async_engine = create_async_engine(async_database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


def load_model_modules() -> None:
    """모든 도메인 모델을 로드해 metadata를 완성한다."""
    for module_path in MODEL_MODULES:
        import_module(module_path)


# auth 도메인 비동기 전환 완료 시 삭제
def get_db():
    """요청 단위 동기 DB 세션 (auth 전용)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """요청 단위 비동기 DB 세션."""
    async with AsyncSessionLocal() as db:
        yield db
