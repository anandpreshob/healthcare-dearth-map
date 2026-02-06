from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://dearth:dearth_pass@db:5432/dearth_map"
    CORS_ORIGINS: str = "http://localhost:3000"
    DEBUG: bool = False

    model_config = {"env_prefix": "", "env_file": ".env"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [s.strip() for s in self.CORS_ORIGINS.split(",")]


settings = Settings()
