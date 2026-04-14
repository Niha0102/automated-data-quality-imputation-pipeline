from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://adqip:adqip_secret@localhost:5432/adqip"

    # MongoDB
    MONGO_URL: str = "mongodb://adqip:adqip_secret@localhost:27017/adqip?authSource=admin"

    # Redis
    REDIS_URL: str = "redis://:adqip_secret@localhost:6379/0"

    # S3 / MinIO
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_DATASETS_BUCKET: str = "adqip-datasets"
    S3_REPORTS_BUCKET: str = "adqip-reports"
    AWS_ACCESS_KEY_ID: str = "adqip_minio"
    AWS_SECRET_ACCESS_KEY: str = "adqip_minio_secret"
    AWS_DEFAULT_REGION: str = "us-east-1"

    # Auth
    JWT_SECRET_KEY: str = "change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC: str = "adqip-stream"
    KAFKA_BATCH_WINDOW_SECONDS: int = 5

    # Pipeline
    QUALITY_SCORE_ALERT_THRESHOLD: float = 70.0
    MAX_UPLOAD_SIZE_BYTES: int = 2 * 1024 * 1024 * 1024  # 2 GB
    CELERY_BROKER_URL: str = "redis://:adqip_secret@localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://:adqip_secret@localhost:6379/1"


settings = Settings()
