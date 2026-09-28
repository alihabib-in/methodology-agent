from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_base_url: str = "http://llm:8080/v1"
    llm_model: str = "qwen3-4b-instruct-2507"
    llm_timeout_seconds: float = 120.0
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1200
    default_language: str = "auto-detect"

    database_url: str = (
        "postgresql+psycopg://methodology:methodology@postgres:5432/methodology"
    )
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "methodology_knowledge"
    embedding_url: str = "http://embedding:8001"
    embedding_model: str = "intfloat/multilingual-e5-small"

    jitsi_base_url: str = "https://localhost:8443"
    jitsi_room_prefix: str = "scad"
    jitsi_jwt_app_id: str = "scad_methodology"
    jitsi_jwt_secret: str = ""
    jitsi_jwt_accepted_issuers: str = "scad_methodology_backend"
    jitsi_jwt_accepted_audiences: str = "scad_methodology_meet"


settings = Settings()
