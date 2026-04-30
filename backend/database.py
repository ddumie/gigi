from importlib import import_module

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from backend.config import settings


MODEL_MODULES = (
    "backend.domains.auth.models",
    "backend.domains.onboarding.models",
    "backend.domains.habits.models",
    "backend.domains.support.models",
    "backend.domains.neighbor.models",
)

# 비동기 엔진
async_database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
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


async def get_async_db():
    """요청 단위 비동기 DB 세션."""
    async with AsyncSessionLocal() as db:
        yield db
