from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./feedback_db.db"
    SECRET_KEY: str = "dev-shared-secret-change-me"
    ALGORITHM: str = "HS256"
    PRODUCT_SERVICE_URL: str = "http://localhost:8003"
    ORDER_SERVICE_URL: str = "http://localhost:8004"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
