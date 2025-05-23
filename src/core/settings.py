from pathlib import Path
from typing import Any

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            Path(__file__).parent.parent.parent.joinpath(".env"),
            Path(__file__).parent.parent.parent.joinpath(".env.dev")
        )
    )

    BASE_DIR: Path = Path(__file__).parent.parent
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_EXTERNAL_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr

    WEBSHARE_API_KEY: SecretStr
    LOG_PATH: str

    def model_post_init(self, context: Any, /) -> None:
        self.LOG_PATH = str(self.BASE_DIR / self.LOG_PATH)

    @property
    def psql_dsn(self) -> SecretStr:
        dsn = (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}"
            f"@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )
        return SecretStr(dsn)
