from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Always locate .env inside the backend folder.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    admin_api_key: str = ""
    aiops_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()