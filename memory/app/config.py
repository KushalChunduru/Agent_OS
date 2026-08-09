from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    memory_host: str = "0.0.0.0"
    memory_port: int = 8001
    database_url: str = "postgresql+asyncpg://agentos:agentos@localhost:5432/agentos"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
