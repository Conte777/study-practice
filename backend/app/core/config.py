from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, sourced from environment variables (and `.env` locally)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    POSTGRES_USER: str = "app"
    POSTGRES_PASSWORD: str = "app"
    POSTGRES_DB: str = "app"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+psycopg://app:app@postgres:5432/app"
    ELASTICSEARCH_URL: str = "http://elasticsearch:9200"
    REDIS_URL: str = "redis://redis:6379/0"
    BACKEND_PORT: int = 8000
    # Comma-separated list of allowed CORS origins.
    CORS_ORIGINS: str = "http://localhost:8080"

    # Auth. Override JWT_SECRET in every real deployment.
    JWT_SECRET: str = "change-me-in-prod"
    JWT_EXPIRE_MINUTES: int = 60 * 24
    # Demo account seeded at startup so the FE/E2E can log in. Empty user disables seeding.
    DEMO_USER: str = "demo"
    DEMO_PASSWORD: str = "demo12345"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
