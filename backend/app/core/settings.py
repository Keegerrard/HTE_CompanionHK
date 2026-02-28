from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(REPO_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = "CompanionHK API"
    app_env: str = Field(default="development", alias="APP_ENV")
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    frontend_origin: str = Field(
        default="http://localhost:3000", alias="FRONTEND_ORIGIN")
    chat_provider: str = Field(default="mock", alias="CHAT_PROVIDER")
    feature_langgraph_enabled: bool = Field(
        default=False, alias="FEATURE_LANGGRAPH_ENABLED")
    langgraph_checkpointer_backend: str = Field(
        default="memory", alias="LANGGRAPH_CHECKPOINTER_BACKEND")

    feature_minimax_enabled: bool = Field(
        default=False, alias="FEATURE_MINIMAX_ENABLED")
    minimax_api_key: str = Field(default="", alias="MINIMAX_API_KEY")
    minimax_model: str = Field(
        default="MiniMax-M2.5", alias="MINIMAX_MODEL")
    minimax_base_url: str = Field(
        default="https://api.minimax.io/v1", alias="MINIMAX_BASE_URL")
    feature_elevenlabs_enabled: bool = Field(
        default=False, alias="FEATURE_ELEVENLABS_ENABLED")
    feature_cantoneseai_enabled: bool = Field(
        default=False, alias="FEATURE_CANTONESEAI_ENABLED")
    feature_exa_enabled: bool = Field(
        default=False, alias="FEATURE_EXA_ENABLED")
    exa_api_key: str = Field(default="", alias="EXA_API_KEY")
    feature_aws_enabled: bool = Field(
        default=True, alias="FEATURE_AWS_ENABLED")
    feature_weather_enabled: bool = Field(
        default=True, alias="FEATURE_WEATHER_ENABLED")
    feature_google_maps_enabled: bool = Field(
        default=True, alias="FEATURE_GOOGLE_MAPS_ENABLED")

    google_maps_api_key: str = Field(default="", alias="GOOGLE_MAPS_API_KEY")
    google_maps_language: str = Field(
        default="en", alias="GOOGLE_MAPS_LANGUAGE")
    google_maps_region: str = Field(default="hk", alias="GOOGLE_MAPS_REGION")
    google_maps_default_radius_meters: int = Field(
        default=5000, alias="GOOGLE_MAPS_DEFAULT_RADIUS_METERS")
    google_maps_transport_mode: str = Field(
        default="walking", alias="GOOGLE_MAPS_TRANSPORT_MODE")
    google_maps_photo_max_width: int = Field(
        default=800, alias="GOOGLE_MAPS_PHOTO_MAX_WIDTH")

    open_meteo_base_url: str = Field(
        default="https://api.open-meteo.com", alias="OPEN_METEO_BASE_URL")
    provider_timeout_seconds: float = Field(
        default=6.0, alias="PROVIDER_TIMEOUT_SECONDS")

    memory_long_term_strategy: str = Field(
        default="hybrid_profile_retrieval", alias="MEMORY_LONG_TERM_STRATEGY")
    memory_retrieval_top_k: int = Field(
        default=5, alias="MEMORY_RETRIEVAL_TOP_K")
    memory_short_term_ttl_seconds: int = Field(
        default=1800, alias="MEMORY_SHORT_TERM_TTL_SECONDS")
    memory_short_term_max_turns: int = Field(
        default=20, alias="MEMORY_SHORT_TERM_MAX_TURNS")
    memory_embedding_model: str = Field(
        default="text-embedding-3-small", alias="MEMORY_EMBEDDING_MODEL")
    memory_embedding_dimensions: int = Field(
        default=1536, alias="MEMORY_EMBEDDING_DIMENSIONS")
    memory_retrieval_source: str = Field(
        default="hybrid_profile_retrieval", alias="MEMORY_RETRIEVAL_SOURCE")
    memory_write_audit_required: bool = Field(
        default=True, alias="MEMORY_WRITE_AUDIT_REQUIRED")

    database_url: str = Field(default="", alias="DATABASE_URL")
    postgres_user: str = Field(default="companion", alias="POSTGRES_USER")
    postgres_password: str = Field(
        default="companion", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="companionhk", alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_timeout_seconds: int = Field(
        default=30, alias="DB_POOL_TIMEOUT_SECONDS")
    db_pool_recycle_seconds: int = Field(
        default=1800, alias="DB_POOL_RECYCLE_SECONDS")
    db_connect_timeout_seconds: int = Field(
        default=1, alias="DB_CONNECT_TIMEOUT_SECONDS")
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    redis_url: str = Field(default="", alias="REDIS_URL")
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")

    privacy_store_precise_user_location: bool = Field(
        default=False, alias="PRIVACY_STORE_PRECISE_USER_LOCATION")
    recommendation_user_location_geohash_precision: int = Field(
        default=6, alias="RECOMMENDATION_USER_LOCATION_GEOHASH_PRECISION")

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        encoded_user = quote_plus(self.postgres_user)
        encoded_password = quote_plus(self.postgres_password)
        return (
            "postgresql+psycopg://"
            f"{encoded_user}:{encoded_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            f"?connect_timeout={self.db_connect_timeout_seconds}"
        )

    @property
    def effective_redis_url(self) -> str:
        if self.redis_url:
            return self.redis_url

        redis_auth = (
            f":{quote_plus(self.redis_password)}@" if self.redis_password else ""
        )
        return f"redis://{redis_auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
