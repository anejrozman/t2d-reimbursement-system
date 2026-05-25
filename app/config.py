"""
Application configuration loaded from environment variables.
All settings have defaults so the service starts without a .env file.
Override by setting environment variables or creating a .env file in the
project root.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the T2D reimbursement service."""

    fhir_base_url: str = "https://hapi.fhir.org/baseR4"
    fhir_timeout: float = 10.0
    app_version: str = "0.1.0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
