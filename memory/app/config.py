from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    memory_host: str = "0.0.0.0"
    memory_port: int = 8001
    database_url: str = "sqlite+aiosqlite:///./memory.db"
    embedding_dim: int = 256

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
