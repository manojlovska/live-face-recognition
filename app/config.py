from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "CelebA Face Similarity API"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", validation_alias="APP_ENVIRONMENT")
    model_id: str = Field(default="celeba-face-similarity-cpu", validation_alias="FACE_MODEL_ID")
    model_asset_dir: str = Field(default="models", validation_alias="MODEL_ASSET_DIR")
    yunet_model_path: str = Field(
        default="models/face_detection_yunet.onnx",
        validation_alias="YUNET_MODEL_PATH",
    )
    sface_model_path: str = Field(
        default="models/face_recognition_sface.onnx",
        validation_alias="SFACE_MODEL_PATH",
    )
    model_manifest_path: str = Field(
        default="models/model_manifest.json",
        validation_alias="MODEL_MANIFEST_PATH",
    )
    model_auto_load: bool = Field(default=False, validation_alias="MODEL_AUTO_LOAD")
    max_image_bytes: int = Field(
        default=5 * 1024 * 1024,
        ge=1,
        validation_alias="FACE_MAX_IMAGE_BYTES",
    )
    face_api_key: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
