# -*- coding: utf-8 -*-
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Config(BaseSettings):
    class Config:
        env_file = ".env"

    ENV: str = "STAG"
    SENTRY_DSN: Optional[str] = None
    REDIS_URL: Optional[str] = None
    POSTGRES_URL: Optional[str] = None
    PREFIX_URL: str = "/"
    PORT: Optional[int] = Field(default=5005)
    ACCESS_TOKEN: str = ""
    ALGORITHM: str = "HS256"
    REDIS_URL: Optional[str] = None


config = Config()
