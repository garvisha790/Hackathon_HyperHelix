from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "change-me-in-production"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/digitalca"
    database_url_sync: str = "postgresql+psycopg://postgres:postgres@localhost:5432/digitalca"
    redis_url: str = "redis://localhost:6379/0"

    aws_region: str = "ap-south-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_bucket_name: str = "digitalca-documents"
    textract_region: str = "ap-south-1"
    bedrock_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"

    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    cognito_region: str = "ap-south-1"

    cors_origins: str = "http://localhost:3000"

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
