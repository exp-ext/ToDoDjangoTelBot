from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='.env')

    @property
    def base_dir(self) -> str:
        return Path(__file__).resolve().parent


settings = Settings()
