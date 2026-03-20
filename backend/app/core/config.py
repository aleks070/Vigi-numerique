from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_URL: str = "postgresql://vigi_user:vigi_password@localhost:5432/vigi"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # API IDFM / PRIM
    IDFM_API_KEY: str = ""
    PRIM_BASE_URL: str = "https://prim.iledefrance-mobilites.fr/marketplace"

    # Auth JWT
    JWT_SECRET: str = "change_me_in_production"
    JWT_EXPIRY: int = 3600

    # Détection
    ALERT_POLL_INTERVAL: int = 60           # secondes
    DELAY_THRESHOLD_SECONDS: int = 180      # 3 minutes
    SUPPRESSION_THRESHOLD: float = 0.2      # 20%

    class Config:
        env_file = ".env"


settings = Settings()
