"""Configuration management using pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        # Don't parse CLI args by default (to avoid conflicts with pytest)
        cli_parse_args=False,
        # Enable implicit boolean flags (--debug instead of --debug true)
        cli_implicit_flags=True,
        cli_kebab_case=True,
    )

    # API Configuration
    api_url: str = Field(
        default="http://localhost/layout-parsing",
        description="API endpoint URL",
    )
    api_key: str = Field(
        default="",
        description="API key for authentication",
    )

    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind to",
    )
    port: int = Field(
        default=7860,
        description="Port to bind to",
    )
    share: bool = Field(
        default=False,
        description="Create a public shareable link",
    )

    # Debug
    debug: bool = Field(
        default=False,
        description="Enable debug mode to log API requests and responses",
    )

    def get_headers(self) -> dict:
        """Get HTTP headers with optional API key."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def to_launch_kwargs(self) -> dict:
        """Convert settings to Gradio launch kwargs."""
        return {
            "server_name": self.host,
            "server_port": self.port,
            "share": self.share,
            "show_error": True,
        }


def get_cli_settings() -> Settings:
    """Get settings from command line arguments.

    This should only be called from the main entry point,
    not from tests or other code.
    """
    return Settings(_cli_parse_args=True)
