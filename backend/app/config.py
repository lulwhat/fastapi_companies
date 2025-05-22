from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    SQL_USER: str
    SQL_PASSWORD: str
    SQL_DATABASE: str
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: str
    EXPORT_QUEUE: str = "export_queue"
    EXPORT_DIR: Path = Path("/home/app/web/app/exports")
    env_file: str = ".env"
    env_file_encoding: str = "utf-8"

    model_config = ConfigDict(from_attributes=True)

    @property
    def RABBITMQ_URL(self) -> str:
        return (f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}"
                f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/")

    @property
    def URL_DATABASE(self) -> str:
        return (f"postgresql+asyncpg://{self.SQL_USER}:{self.SQL_PASSWORD}"
                f"@db:5432/{self.SQL_DATABASE}")

    # local debug version
    @property
    def URL_DATABASE_DEBUG(self) -> str:
        return (f"postgresql+asyncpg://{self.SQL_USER}:{self.SQL_PASSWORD}"
                f"@localhost:5432/{self.SQL_DATABASE}")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
