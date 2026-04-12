from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Medical AI Workflow Demo API"
    environment: str = "development"
    database_url: str = "postgresql://demo_user:demo_password@localhost:5432/medical_ai_demo"
    redis_url: str = "redis://localhost:6379/0"
    cors_origin: str = "http://localhost:5173"
    stale_run_timeout_minutes: int = 5

    keycloak_public_url: str = "http://localhost:8080"
    keycloak_internal_url: str = "http://keycloak:8080"
    keycloak_realm: str = "etl-demo"
    keycloak_client_id: str = "etl-frontend"

    @property
    def keycloak_issuer(self) -> str:
        return f"{self.keycloak_public_url}/realms/{self.keycloak_realm}"

    @property
    def oidc_discovery_url(self) -> str:
        return f"{self.keycloak_internal_url}/realms/{self.keycloak_realm}/.well-known/openid-configuration"

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgresql+psycopg://"):
            return self.database_url
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
