from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CelebA Face Similarity API"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", validation_alias="APP_ENVIRONMENT")
    model_id: str = Field(default="celeba-face-similarity-cpu", validation_alias="FACE_MODEL_ID")
    face_api_key: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
