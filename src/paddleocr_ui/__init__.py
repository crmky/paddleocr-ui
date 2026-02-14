"""PaddleOCR-VL Web UI - A modern Gradio interface for PaddleOCR-VL model."""

from .app import create_app, main
from .config import Settings, get_cli_settings

__version__ = "0.1.0"
__all__ = ["create_app", "main", "Settings", "get_cli_settings"]
