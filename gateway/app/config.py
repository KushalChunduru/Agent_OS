from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8000
    jwt_secret: str = "changeme-dev-secret"
    rate_limit_per_minute: int = 60
    redis_url: str = "redis://localhost:6379/0"
    memory_service_url: str = "http://localhost:8001"
    dashboard_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
