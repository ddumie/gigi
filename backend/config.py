import os

from pydantic_settings import BaseSettings, SettingsConfigDict


env_file = os.environ.get("ENV_FILE", ".env")


class Settings(BaseSettings):
    """서비스 전역 설정."""

    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    POSTGRES_DB: str | None = None
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_HOST: str | None = None
    DATABASE_URL: str | None = None
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    GEMINI_API_KEY: str

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.POSTGRES_USER and self.POSTGRES_PASSWORD and self.POSTGRES_HOST and self.POSTGRES_DB:
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:5432/{self.POSTGRES_DB}"
        raise ValueError(
            "DATABASE_URL or all POSTGRES_* settings must be configured for the application to start."
        )


settings = Settings()
