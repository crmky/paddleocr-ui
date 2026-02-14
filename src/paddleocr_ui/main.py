"""Entry point for PaddleOCR-VL Web UI."""

from paddleocr_ui.app import create_app
from paddleocr_ui.config import get_cli_settings


def main():
    """Main entry point.
    
    Settings are automatically parsed from command line arguments.
    Use --help to see all available options.
    """
    # Settings are parsed from CLI arguments
    settings = get_cli_settings()
    
    if settings.debug:
        print("🐛 Debug mode enabled")
    
    print(f"🚀 Starting PaddleOCR-VL Web UI...")
    print(f"   URL: http://{settings.host}:{settings.port}")
    print(f"   API: {settings.api_url}")
    
    # Create and launch the app
    app, launch_kwargs = create_app(settings)
    
    # Add server settings to launch kwargs
    launch_kwargs.update(settings.to_launch_kwargs())
    
    app.launch(**launch_kwargs)


if __name__ == "__main__":
    main()
