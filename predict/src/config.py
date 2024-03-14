from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(env_prefix='MODEL_')

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent


settings = Settings()
