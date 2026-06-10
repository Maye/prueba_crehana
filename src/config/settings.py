from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5434/crehana"
    app_name: str = "Crehana Task Manager"
    debug: bool = False
    secret_key: str = "changeme-use-a-real-secret-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = {"env_file": ".env"}


settings = Settings()
