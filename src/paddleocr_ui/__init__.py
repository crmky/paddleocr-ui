"""PaddleOCR-VL Web UI - A modern Gradio interface for PaddleOCR-VL model."""

from paddleocr_ui.app import create_app
from paddleocr_ui.config import Settings, get_cli_settings
from paddleocr_ui.main import main

__version__ = "0.1.0"
__all__ = ["create_app", "main", "Settings", "get_cli_settings"]
