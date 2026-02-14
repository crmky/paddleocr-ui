"""Unit tests for configuration management."""

import sys
from unittest.mock import patch

from paddleocr_ui.config import Settings, get_cli_settings


class TestSettings:
    """Test cases for Settings class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        settings = Settings()

        assert settings.api_url == "http://paddleocr.home/layout-parsing"
        assert settings.api_key == ""
        assert settings.host == "0.0.0.0"
        assert settings.port == 7860
        assert settings.share is False
        assert settings.debug is False

    def test_custom_values(self):
        """Test that custom values can be set."""
        settings = Settings(
            api_url="http://localhost:8080/predict",
            api_key="test-key-123",
            host="127.0.0.1",
            port=9000,
            share=True,
            debug=True,
        )

        assert settings.api_url == "http://localhost:8080/predict"
        assert settings.api_key == "test-key-123"
        assert settings.host == "127.0.0.1"
        assert settings.port == 9000
        assert settings.share is True
        assert settings.debug is True

    def test_get_headers_without_api_key(self):
        """Test get_headers returns correct headers without API key."""
        settings = Settings(api_key="")
        headers = settings.get_headers()

        assert headers == {"Content-Type": "application/json"}
        assert "Authorization" not in headers

    def test_get_headers_with_api_key(self):
        """Test get_headers returns correct headers with API key."""
        settings = Settings(api_key="my-secret-key")
        headers = settings.get_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer my-secret-key"


class TestCliSettings:
    """Test cases for CLI argument parsing."""

    def test_cli_parse_args_default(self):
        """Test CLI parsing with default args (only prog name)."""
        with patch.object(sys, "argv", ["test"]):
            settings = get_cli_settings()

        assert settings.api_url == "http://paddleocr.home/layout-parsing"
        assert settings.api_key == ""
        assert settings.host == "0.0.0.0"
        assert settings.port == 7860
        assert settings.share is False
        assert settings.debug is False

    def test_cli_parse_args_custom(self):
        """Test CLI parsing with custom arguments.

        cli_implicit_flags allows --flag syntax for booleans.
        """
        with patch.object(
            sys,
            "argv",
            [
                "paddleocr-ui",
                "--api-url",
                "http://localhost:8080/predict",
                "--api-key",
                "secret-key",
                "--host",
                "127.0.0.1",
                "--port",
                "9000",
                "--share",
                "--debug",
            ],
        ):
            settings = get_cli_settings()

        assert settings.api_url == "http://localhost:8080/predict"
        assert settings.api_key == "secret-key"
        assert settings.host == "127.0.0.1"
        assert settings.port == 9000
        assert settings.share is True
        assert settings.debug is True
