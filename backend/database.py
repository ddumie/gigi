from importlib import import_module

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings


MODEL_MODULES = (
    "backend.domains.auth.models",
    "backend.domains.onboarding.models",
    "backend.domains.habits.models",
    "backend.domains.support.models",
    "backend.domains.neighbor.models",
)

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


def load_model_modules() -> None:
    """모든 도메인 모델을 로드해 metadata를 완성한다."""
    for module_path in MODEL_MODULES:
        import_module(module_path)


def get_db():
    """요청 단위 DB 세션."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
