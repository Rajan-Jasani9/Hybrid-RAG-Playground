try:
    from pydantic_settings import BaseSettings
except Exception:
    from pydantic import BaseSettings

from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL")


settings = Settings()