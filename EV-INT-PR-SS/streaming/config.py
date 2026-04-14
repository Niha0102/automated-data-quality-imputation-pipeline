from pydantic_settings import BaseSettings, SettingsConfigDict


class StreamingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC: str = "adqip-stream"
    KAFKA_BATCH_WINDOW_SECONDS: int = 5
    KAFKA_GROUP_ID: str = "adqip-ingestor"

    # Internal API to submit jobs
    BACKEND_API_URL: str = "http://backend:8000"
    BACKEND_API_TOKEN: str = ""

    LOG_LEVEL: str = "INFO"


settings = StreamingSettings()
