"""
config.py — Application-wide settings loaded from environment variables.

All settings are validated by Pydantic BaseSettings. Override any value
by setting the corresponding environment variable or by editing .env.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_env: str = Field(default="development", description="Runtime environment")
    app_log_level: str = Field(default="INFO")
    secret_key: str = Field(default="change-me-in-production")

    # ── LLM Provider ─────────────────────────────────────────────────────────
    llm_provider: str = Field(default="openai", description="openai | gemini | deepseek")
    llm_model: str = Field(default="gpt-4o")
    openai_api_key: str = Field(default="")
    gemini_api_key: str = Field(default="")
    deepseek_api_key: str = Field(default="")

    # ── Neo4j ─────────────────────────────────────────────────────────────────
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="")

    # ── Vector DB ─────────────────────────────────────────────────────────────
    vector_db_backend: str = Field(default="pinecone", description="pinecone | milvus")
    pinecone_api_key: str = Field(default="")
    pinecone_environment: str = Field(default="us-east-1-aws")
    pinecone_index_name: str = Field(default="fillado-embeddings")
    milvus_uri: str = Field(default="http://localhost:19530")
    milvus_collection_name: str = Field(default="fillado_embeddings")

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/fillado"
    )

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ── External Data Sources ─────────────────────────────────────────────────
    et_markets_base_url: str = Field(
        default="https://economictimes.indiatimes.com/markets"
    )
    nse_api_base_url: str = Field(default="https://www.nseindia.com/api")


settings = Settings()
