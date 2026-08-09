from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    memory_host: str = "0.0.0.0"
    memory_port: int = 8001
    qdrant_path: str = "./qdrant_data"
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "all-minilm"
    embedding_dim: int = 384

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
