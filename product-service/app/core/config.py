from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./product_db.db"
    SECRET_KEY: str = "dev-shared-secret-change-me"
    ALGORITHM: str = "HS256"
    INTERNAL_API_KEY: str = "dev-internal-api-key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
