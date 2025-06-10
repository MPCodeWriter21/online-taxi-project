"""This file contains the application configuration."""

# yapf: disable

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# yapf: enable


class Settings(BaseSettings):
    """This class contains all the application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    # Basic settings
    DEBUG: bool = False
    DOMAIN: str = "localhost"
    HTTPS: bool = False
    ENVIRONMENT: str = "local"
    ALLOWED_HOSTS: list[str] = ["*"]

    # Security settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    CSRF_SECRET_KEY: str = "your-csrf-secret-key-change-this-in-production"
    FERNET_SECRET_KEY: str = "your-fernet-key-must-be-32-url-safe-base64-encoded-bytes="

    # Database settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "app"

    @computed_field
    @property
    def site_url(self) -> str:
        """Construct the site URL from the domain."""
        protocol = "https" if self.HTTPS else "http"
        return f"{protocol}://{self.DOMAIN}"

    @computed_field
    @property
    def database_url(self) -> str:
        """Construct the database URL."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @computed_field
    @property
    def async_database_url(self) -> str:
        """Construct the async database URL."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
