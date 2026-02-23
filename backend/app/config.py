try:
    from pydantic_settings import BaseSettings
except Exception:
    from pydantic import BaseSettings

from pydantic import Field
import os
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., env="DATABASE_URL")


settings = Settings()