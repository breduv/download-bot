from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    bot_token: SecretStr

    spotify_client_id: str

    spotify_client_secret: SecretStr

    media_proxy: SecretStr | None = Field(default=None)

    telegram_proxy: SecretStr | None = Field(default=None)

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = Field(default="INFO")

    @field_validator("media_proxy", "telegram_proxy", mode="before")
    @classmethod
    def empty_proxy_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()