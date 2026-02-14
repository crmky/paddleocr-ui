# AGENTS.md - PaddleOCR-VL Web UI

## Project Overview

**PaddleOCR-VL Web UI** is a modern, clean web interface for the PaddleOCR-VL model built with [Gradio](https://gradio.app/). It provides three main OCR functionalities:

1. **📑 Document Parsing**: Full-page document analysis with layout detection (supports images & multi-page PDFs)
2. **🎯 Element Recognition**: Targeted recognition for text, formulas, tables, charts, and seals
3. **👁️ Spotting**: Detect and locate specific elements in images

The application acts as a client to a PaddleOCR API backend, sending images and displaying processed results with markdown rendering, visualization, and raw output tabs.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.14+ |
| Web Framework | Gradio 5.0+ |
| Image Processing | Pillow |
| HTTP Client | requests |
| Configuration | pydantic-settings |
| Build System | Hatchling |
| Testing | pytest |

## Project Structure

```
paddleocr-ui/
├── pyproject.toml          # Project configuration and dependencies
├── README.md               # User-facing documentation
├── AGENTS.md               # This file - AI agent documentation
├── .python-version         # Python version (3.14)
├── .gitignore              # Git ignore patterns
├── src/
│   └── paddleocr_ui/       # Main package
│       ├── __init__.py     # Package exports
│       ├── main.py         # CLI entry point
│       ├── app.py          # Gradio UI definition (~650 lines)
│       ├── config.py       # Pydantic settings management
│       ├── api.py          # API client for PaddleOCR backend
│       ├── handlers.py     # Business logic for Gradio callbacks
│       └── utils.py        # Utility functions (image processing, etc.)
└── tests/
    └── test_config.py      # Unit tests for configuration
```

## Module Responsibilities

| Module | Purpose |
|--------|---------|
| `main.py` | Entry point, parses CLI args and launches the Gradio app |
| `app.py` | Defines the complete Gradio UI with tabs, components, event handlers |
| `config.py` | Settings class using pydantic-settings with CLI parsing support |
| `api.py` | HTTP client for calling PaddleOCR API, handles request/response processing |
| `handlers.py` | Business logic wrappers called by Gradio event handlers |
| `utils.py` | Helper functions: base64 encoding, image preview, LaTeX escaping |

## Build and Run Commands

### Installation

```bash
# Install in editable mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### Running the Application

```bash
# Default - runs on http://0.0.0.0:7860
python -m paddleocr_ui

# Or use the entry point
paddleocr-ui

# Custom API endpoint and authentication
python -m paddleocr_ui --api-url http://your-api-endpoint/predict --api-key your-key

# Custom host and port
python -m paddleocr_ui --host 0.0.0.0 --port 8080

# Create a public shareable link
python -m paddleocr_ui --share

# Enable debug mode (logs API requests/responses)
python -m paddleocr_ui --debug

# Show all available options
python -m paddleocr_ui --help
```

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_config.py
```

## Configuration

Configuration is provided via **command line arguments** using `pydantic-settings`:

| Option | Default | Description |
|--------|---------|-------------|
| `--api-url` | `http://localhost/layout-parsing` | PaddleOCR API endpoint |
| `--api-key` | (none) | API key for authentication |
| `--host` | `0.0.0.0` | Server host to bind |
| `--port` | `7860` | Server port |
| `--share` | false | Create public shareable link |
| `--debug` | false | Log API requests/responses |

The `Settings` class in `config.py` uses `cli_implicit_flags=True`, so boolean flags work as `--debug` instead of `--debug true`.

## Code Style Guidelines

1. **Type Hints**: Use Python 3.10+ type hints (`str | None`, `list[str]`)
2. **Docstrings**: All modules and functions have descriptive docstrings
3. **Imports**: Grouped as: stdlib → third-party → local
4. **Naming**: 
   - `snake_case` for functions/variables
   - `PascalCase` for classes
   - `SCREAMING_SNAKE_CASE` for constants
5. **String Quotes**: Use double quotes for strings
6. **Line Length**: Follow PEP 8 (no strict limit observed in codebase)

## Key Implementation Details

### API Communication

The `api.py` module handles communication with the PaddleOCR backend:

- **Endpoint**: POST to configured `api_url`
- **Payload**: JSON with `file` (base64 or URL), `useLayoutDetection`, `promptLabel`, etc.
- **File Types**: Supports images and PDFs (file_type: 0=PDF, 1=image)
- **Response**: JSON with `errorCode`, `result.layoutParsingResults[]`

### Image Processing

- Files are converted to base64 for API transmission via `file_to_base64()`
- Base64 responses are converted to data URLs via `process_base64_image()`
- PDF files show a placeholder icon in preview

### LaTeX/Math Rendering

The app configures LaTeX delimiters for formula rendering:
- `$$...$$` and `\[...\]` for display math
- `$...$` and `\(...\)` for inline math

Inequality symbols (`<`, `>`, `<=`, `>=`) in math are escaped to LaTeX equivalents to prevent HTML parsing issues.

### UI Architecture

- Three main tabs: Document Parsing, Element Recognition, Spotting
- Each tab has left (input) and right (results) columns
- Results display in three sub-tabs: Markdown preview, Visualization, Source code
- Custom CSS provides a modern, professional appearance

## Testing Strategy

Tests are located in `tests/` directory using pytest:

- `test_config.py`: Unit tests for Settings class
  - Default value testing
  - Custom value setting
  - Header generation (with/without API key)
  - CLI argument parsing

When writing tests, **avoid calling `get_cli_settings()`** in import-time code (it parses `sys.argv`). Use `Settings()` directly in tests.

## Debugging

Enable debug mode with `--debug` to see:
- Full request payload (base64 data truncated for readability)
- Full API response (base64 data truncated)

This is useful for verifying API communication without the UI layer.

## Security Considerations

1. **API Keys**: Passed via `Authorization: Bearer` header
2. **File Uploads**: Limited to images and PDFs via `file_types` parameter
3. **No Persistent Storage**: Uploaded files are processed in memory/temp files
4. **Base64 Handling**: Large files are handled as base64 strings

## Common Tasks for Agents

### Adding a New Recognition Type

1. Add button in Element Recognition tab (`app.py`)
2. Add mapping in `recognition_mapping` list
3. Add handler mapping in `handlers.py` `handle_targeted_recognition()`
4. Update `call_api()` if new prompt labels are needed

### Modifying API Payload

Edit `call_api()` in `api.py`:
- Add parameters to function signature
- Include in `payload` dict
- Add debug logging if needed

### Styling Changes

The `CUSTOM_CSS` variable in `app.py` contains all custom styling:
- CSS variables for colors in `:root`
- Component-specific styles (buttons, tabs, etc.)
- Responsive adjustments in `@media` queries
