# PaddleOCR-VL Web UI

A modern, clean web interface for PaddleOCR-VL model built with Gradio.

## Features

- 📑 **Document Parsing**: Full-page document analysis with layout detection
- 🎯 **Element Recognition**: Targeted recognition for text, formulas, tables, charts, and seals
- 🔍 **Spotting**: Detect and locate specific elements in images
- 🖼️ **Base64 Image Support**: Handles both URL and Base64-encoded images from API
- 📱 **Responsive Design**: Modern UI that works on desktop and mobile

## Installation

```bash
# Install dependencies
pip install -e .

# Or install directly
pip install gradio pillow requests
```

## Usage

```bash
# Run with default settings
python -m paddleocr_ui

# Or use the entry point
paddleocr-ui

# Custom API endpoint and authentication
python -m paddleocr_ui --api-url http://your-api-endpoint/predict --api-key your-key

# Custom host and port
python -m paddleocr_ui --host 0.0.0.0 --port 8080

# Create a public shareable link
python -m paddleocr_ui --share

# Enable debug mode to log API requests and responses
python -m paddleocr_ui --debug

# Show all available options
python -m paddleocr_ui --help
```

### Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--api-url` | `http://paddleocr.home/layout-parsing` | API endpoint URL |
| `--api-key` | (none) | API key for authentication |
| `--host` | `0.0.0.0` | Host to bind to |
| `--port` | `7860` | Port to bind to |
| `--share` | (disabled) | Create a public shareable link |
| `--debug` | (disabled) | Enable debug mode |

### Debug Mode

When debug mode is enabled (`--debug`), the application will log:
- Full request payload to stdout (with base64 image data truncated for readability)
- Full API response to stdout (with base64 image data truncated)

This is useful for debugging API issues and comparing requests with direct API calls.

## API Response Format

The application expects API responses with the following structure:

```json
{
  "errorCode": 0,
  "result": {
    "layoutParsingResults": [
      {
        "markdown": {
          "text": "# Document content...",
          "images": {
            "image1": "base64-encoded-string-or-url"
          }
        },
        "outputImages": {
          "visualization": "base64-encoded-string-or-url"
        }
      }
    ]
  }
}
```

Images in the response can be either:
- **Base64 encoded strings**: Will be converted to data URLs
- **HTTP URLs**: Will be used directly

## License

MIT License
