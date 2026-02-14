"""
PaddleOCR-VL Web UI - A modern Gradio interface for PaddleOCR-VL model.
"""

import base64
import io
import json
import os
import re
from typing import Dict, List, Tuple, Any, Optional
import time
import requests
from PIL import Image
import gradio as gr
from urllib.parse import urlparse


# Configuration (set via command line arguments)
API_URL = "http://paddleocr.home/layout-parsing"
API_KEY = ""
DEBUG = False

# LaTeX delimiters for formula rendering
LATEX_DELIMITERS = [
    {"left": "$$", "right": "$$", "display": True},
    {"left": "$", "right": "$", "display": False},
    {"left": "\\(", "right": "\\)", "display": False},
    {"left": "\\[", "right": "\\]", "display": True},
]

# Request headers
HEADERS = {"Content-Type": "application/json"}


def image_to_base64_data_url(filepath: str) -> str:
    """Convert local image file to base64 data URL."""
    try:
        ext = os.path.splitext(filepath)[1].lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        mime_type = mime_types.get(ext, "image/jpeg")
        with open(filepath, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return f"data:{mime_type};base64,{encoded_string}"
    except Exception as e:
        print(f"Error encoding image to Base64: {e}")
        return ""


def file_to_base64(path_or_url: str) -> Tuple[str, int]:
    """Convert file path or URL to base64 string and file type.
    
    Returns:
        Tuple of (base64_string, file_type) where file_type is:
        - 0 for PDF file
        - 1 for image file
    """
    if not path_or_url:
        raise ValueError("Please upload a file first.")

    is_url = isinstance(path_or_url, str) and path_or_url.startswith(("http://", "https://"))
    content: bytes

    if is_url:
        r = requests.get(path_or_url, timeout=60)
        r.raise_for_status()
        content = r.content
        ext = os.path.splitext(urlparse(path_or_url).path)[1].lower()
    else:
        ext = os.path.splitext(path_or_url)[1].lower()
        with open(path_or_url, "rb") as f:
            content = f.read()

    # file_type: 0 for PDF, 1 for image (according to PaddleOCR API docs)
    file_type = 0 if ext == ".pdf" else 1
    return base64.b64encode(content).decode("utf-8"), file_type


def escape_inequalities_in_math(md: str) -> str:
    """Escape inequality symbols in math expressions to prevent HTML parsing issues."""
    math_patterns = [
        re.compile(r"\$\$([\s\S]+?)\$\$"),
        re.compile(r"\$([^\$]+?)\$"),
        re.compile(r"\\\[([\s\S]+?)\\\]"),
        re.compile(r"\\\(([\s\S]+?)\\\)"),
    ]

    def fix(s: str) -> str:
        s = s.replace("<=", r" \le ").replace(">=", r" \ge ")
        s = s.replace("≤", r" \le ").replace("≥", r" \ge ")
        s = s.replace("<", r" \lt ").replace(">", r" \gt ")
        return s

    for pat in math_patterns:
        md = pat.sub(lambda m: m.group(0).replace(m.group(1), fix(m.group(1))), md)
    return md


def render_image_preview(path_or_url: str) -> str:
    """Render image preview HTML."""
    if not path_or_url:
        return ""
    
    # Check if it's a PDF file
    ext = os.path.splitext(path_or_url)[1].lower()
    if ext == ".pdf":
        # PDF preview - show a placeholder icon
        return '''<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px;color:#64748b;"><div style="width:80px;height:100px;background:linear-gradient(135deg,#f87171 0%,#dc2626 100%);border-radius:8px;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 6px rgba(0,0,0,0.1);margin-bottom:12px;"><span style="color:white;font-size:24px;font-weight:bold;">PDF</span></div><span style="font-size:14px;">PDF Document</span></div>'''
    
    # Image preview
    is_url = isinstance(path_or_url, str) and path_or_url.startswith(("http://", "https://"))
    if is_url:
        src = path_or_url
    else:
        src = image_to_base64_data_url(path_or_url)
    
    return f'<img src="{src}" alt="Preview" loading="lazy" />'


def update_preview_visibility(path_or_url: Optional[str]) -> Dict:
    """Update preview visibility based on input."""
    if path_or_url:
        html_content = render_image_preview(path_or_url)
        return gr.update(value=html_content, visible=True)
    else:
        return gr.update(value="", visible=False)


def call_api(
    path_or_url: str,
    use_layout_detection: bool,
    prompt_label: Optional[str] = None,
    use_chart_recognition: bool = False,
    use_doc_unwarping: bool = True,
    use_doc_orientation_classify: bool = True,
) -> Dict[str, Any]:
    """Call the PaddleOCR API with the given parameters."""
    is_url = isinstance(path_or_url, str) and path_or_url.startswith(("http://", "https://"))

    if is_url:
        payload = {
            "file": path_or_url,
            "useLayoutDetection": bool(use_layout_detection),
            "useDocUnwarping": use_doc_unwarping,
            "useDocOrientationClassify": use_doc_orientation_classify,
        }
    else:
        b64, file_type = file_to_base64(path_or_url)
        payload = {
            "file": b64,
            "useLayoutDetection": bool(use_layout_detection),
            "fileType": file_type,
            "useDocUnwarping": use_doc_unwarping,
            "useDocOrientationClassify": use_doc_orientation_classify,
        }

    if not use_layout_detection:
        if not prompt_label:
            raise ValueError("Please select a recognition type.")
        payload["promptLabel"] = prompt_label.strip().lower()

    if use_layout_detection and use_chart_recognition:
        payload["useChartRecognition"] = True

    # Debug: dump request payload
    if DEBUG:
        print("=" * 60)
        print("DEBUG: API Request Payload")
        print("=" * 60)
        # Create a copy for logging to avoid modifying the original payload
        log_payload = payload.copy()
        # Truncate base64 image data for readability
        if "file" in log_payload and isinstance(log_payload["file"], str):
            file_data = log_payload["file"]
            if len(file_data) > 200:
                log_payload["file"] = f"{file_data[:100]}...({len(file_data)} chars)...{file_data[-50:]}"
        print(json.dumps(log_payload, indent=2, ensure_ascii=False))
        print("=" * 60)

    try:
        print(f"Sending API request to {API_URL}...")
        resp = requests.post(API_URL, json=payload, headers=HEADERS, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        
        # Debug: dump response
        if DEBUG:
            print("-" * 60)
            print("DEBUG: API Response")
            print("-" * 60)
            # Truncate base64 image data in response for readability
            log_data = json.dumps(data, ensure_ascii=False)
            # Find and truncate base64 strings in response
            import re
            def truncate_base64(match):
                full = match.group(0)
                if len(full) > 200:
                    return f'{full[:100]}...({len(full)} chars)...{full[-50:]}"'
                return full
            log_data = re.sub(r'"[A-Za-z0-9+/]{200,}={0,2}"', truncate_base64, log_data)
            print(log_data[:8000] if len(log_data) > 8000 else log_data)
            if len(log_data) > 8000:
                print(f"... (response truncated, total {len(log_data)} chars)")
            print("=" * 60)
            
    except Exception as e:
        print(f"API request failed: {e}")
        raise gr.Error(f"API request failed: {e}")

    if data.get("errorCode", -1) != 0:
        error_msg = data.get("errorMsg", "Unknown error")
        raise gr.Error(f"API error: {error_msg}")

    return data


def process_base64_image(base64_data: str) -> str:
    """Process base64 image data to display in HTML/Markdown.
    
    Handles both raw base64 strings and data URLs.
    """
    if not base64_data:
        return ""
    
    # If already a data URL, return as is
    if base64_data.startswith("data:"):
        return base64_data
    
    # Otherwise, wrap as JPEG data URL (most common)
    return f"data:image/jpeg;base64,{base64_data}"


def process_api_response(result: Dict[str, Any]) -> Tuple[str, str, str]:
    """Process API response and extract markdown, visualization, and raw markdown.
    
    Handles Base64 encoded images and supports multi-page PDFs.
    """
    layout_results = (result or {}).get("layoutParsingResults", [])
    if not layout_results:
        return "No content was recognized.", "<p>No visualization available.</p>", ""

    all_md_parts = []
    all_images = []
    
    # Process each page
    for page_idx, page in enumerate(layout_results):
        if not page:
            continue
        
        md_data = page.get("markdown") or {}
        md_text = md_data.get("text", "") or ""
        md_images_map = md_data.get("images", {})
        
        # Replace image placeholders
        if md_images_map:
            for placeholder_path, image_data in md_images_map.items():
                if isinstance(image_data, str):
                    image_src = image_data if image_data.startswith("http") else process_base64_image(image_data)
                    md_text = md_text.replace(f'src="{placeholder_path}"', f'src="{image_src}"').replace(f']({placeholder_path})', f']({image_src})')
        
        # Add page separator
        if len(layout_results) > 1 and page_idx > 0:
            all_md_parts.append(f"\n\n---\n\n**Page {page_idx + 1}**\n\n")
        all_md_parts.append(md_text)
        
        # Collect visualization images
        out_imgs = page.get("outputImages") or {}
        for key in sorted(out_imgs.keys()):
            img_data = out_imgs[key]
            if img_data and isinstance(img_data, str):
                all_images.append(img_data if img_data.startswith("http") else process_base64_image(img_data))
    
    # Combine markdown
    combined_md = escape_inequalities_in_math("\n\n".join(all_md_parts))
    
    # Build visualization HTML
    if all_images:
        vis_parts = []
        for idx, img_src in enumerate(all_images):
            if len(layout_results) > 1:
                vis_parts.append(f'<p style="text-align:center;color:#64748b;margin:8px 0;">Page {idx + 1}</p>')
            vis_parts.append(f'<img src="{img_src}" alt="Page {idx + 1}" loading="lazy" style="max-width:100%;margin-bottom:16px;">')
        output_html = "\n".join(vis_parts)
    else:
        output_html = "<p style='text-align:center;color:#888;'>No visualization available.</p>"
    
    return combined_md or "(Empty result)", output_html, combined_md


def handle_document_parsing(
    path_or_url: str,
    use_chart_recognition: bool,
    use_doc_unwarping: bool,
    use_doc_orientation_classify: bool,
) -> Tuple[str, str, str]:
    """Handle document parsing mode."""
    if not path_or_url:
        raise gr.Error("Please upload an image first.")

    data = call_api(
        path_or_url,
        use_layout_detection=True,
        prompt_label=None,
        use_chart_recognition=use_chart_recognition,
        use_doc_unwarping=use_doc_unwarping,
        use_doc_orientation_classify=use_doc_orientation_classify,
    )
    result = data.get("result", {})
    return process_api_response(result)


def handle_targeted_recognition(
    path_or_url: str,
    prompt_choice: str,
) -> Tuple[str, str, str]:
    """Handle targeted recognition mode (OCR, formula, table, etc.)."""
    if not path_or_url:
        raise gr.Error("Please upload an image first.")

    mapping = {
        "Text Recognition": "ocr",
        "Formula Recognition": "formula",
        "Table Recognition": "table",
        "Chart Recognition": "chart",
        "Spotting": "spotting",
        "Seal Recognition": "seal",
    }
    label = mapping.get(prompt_choice, "ocr")

    data = call_api(
        path_or_url,
        use_layout_detection=False,
        prompt_label=label,
        use_doc_unwarping=False,
        use_doc_orientation_classify=False,
    )
    result = data.get("result", {})

    md_preview, _, md_raw = process_api_response(result)
    vis_html = "<p style='text-align:center; color:#888;'>No visualization available.</p>"

    # Special handling for spotting mode
    if label == "spotting":
        page0 = (result.get("layoutParsingResults") or [])[0] or {}
        pruned = page0.get("prunedResult") or {}
        spotting_res = pruned.get("spotting_res") or {}
        md_raw = json.dumps(spotting_res, ensure_ascii=False, indent=2)

        # Get spotting visualization image (base64 format)
        out_imgs = page0.get("outputImages") or {}
        img_data = out_imgs.get("spotting_res_img")
        if img_data:
            if isinstance(img_data, str):
                if img_data.startswith("http"):
                    vis_html = f'<img src="{img_data}" alt="Spotting Visualization" loading="lazy">'
                else:
                    img_src = process_base64_image(img_data)
                    vis_html = f'<img src="{img_src}" alt="Spotting Visualization" loading="lazy">'

        return md_preview, md_raw, vis_html

    return md_preview, md_raw, vis_html


# Modern, clean CSS with a professional color scheme
CUSTOM_CSS = """
:root {
    --primary-color: #4f46e5;
    --primary-hover: #4338ca;
    --secondary-color: #06b6d4;
    --bg-color: #f8fafc;
    --card-bg: #ffffff;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --border-color: #e2e8f0;
    --success-color: #10b981;
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
}

/* Base styles */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%) !important;
    min-height: 100vh;
}

/* Tab styles */
.tabs {
    background: transparent !important;
    border: none !important;
}

.tab-nav {
    background: var(--card-bg) !important;
    border-radius: var(--radius-md) !important;
    padding: 6px !important;
    box-shadow: var(--shadow-sm) !important;
    border: 1px solid var(--border-color) !important;
    margin-bottom: 20px !important;
    gap: 4px !important;
}

.tab-nav button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 12px 24px !important;
    border: none !important;
    background: transparent !important;
    color: var(--text-secondary) !important;
    transition: all 0.2s ease !important;
}

.tab-nav button:hover {
    background: #f1f5f9 !important;
    color: var(--text-primary) !important;
}

.tab-nav button.selected {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%) !important;
    color: white !important;
    box-shadow: var(--shadow-sm) !important;
}

/* Card styles */
.card {
    background: var(--card-bg) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-md) !important;
    border: 1px solid var(--border-color) !important;
    padding: 20px !important;
}

/* Button styles */
button.primary {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    padding: 12px 28px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: white !important;
    box-shadow: var(--shadow-md) !important;
    transition: all 0.2s ease !important;
}

button.primary:hover {
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-lg) !important;
    opacity: 0.95 !important;
}

button.secondary {
    background: #f1f5f9 !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius-sm) !important;
    padding: 10px 20px !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
    transition: all 0.2s ease !important;
}

button.secondary:hover {
    background: #e2e8f0 !important;
    border-color: #cbd5e1 !important;
}

/* Button grid for recognition types */
.button-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)) !important;
    gap: 10px !important;
    margin-top: 12px !important;
}

.button-grid button {
    height: 44px !important;
    font-size: 0.9rem !important;
}

/* File upload styles */
.file-upload {
    border: 2px dashed var(--border-color) !important;
    border-radius: var(--radius-md) !important;
    background: #f8fafc !important;
    transition: all 0.2s ease !important;
}

.file-upload:hover {
    border-color: var(--primary-color) !important;
    background: #f0f9ff !important;
}

/* Image preview styles */
.image-preview-container {
    background: var(--card-bg) !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border-color) !important;
    overflow: hidden !important;
    min-height: 300px !important;
    max-height: 500px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.image-preview-container img {
    max-width: 100% !important;
    max-height: 480px !important;
    object-fit: contain !important;
}

/* Checkbox styles */
.checkbox-row {
    display: flex !important;
    gap: 16px !important;
    flex-wrap: wrap !important;
}

.checkbox-row label {
    background: #f1f5f9 !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius-sm) !important;
    padding: 10px 16px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    font-size: 0.9rem !important;
}

.checkbox-row label:hover {
    background: #e2e8f0 !important;
}

.checkbox-row input:checked + label,
.checkbox-row label:has(input:checked) {
    background: #dbeafe !important;
    border-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
}

/* Result tabs */
.result-tabs {
    background: var(--card-bg) !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border-color) !important;
}

.result-tabs .tab-nav {
    background: #f8fafc !important;
    border-bottom: 1px solid var(--border-color) !important;
    border-radius: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

.result-tabs .tab-nav button {
    border-radius: 0 !important;
    padding: 14px 20px !important;
    font-size: 0.9rem !important;
}

.result-tabs .tab-nav button.selected {
    background: white !important;
    color: var(--primary-color) !important;
    box-shadow: inset 0 -2px 0 var(--primary-color) !important;
}

/* Tab content - only active tab is visible */
.result-tabs .tabitem {
    max-height: calc(100vh - 280px) !important;
    overflow: auto !important;
}

/* Hide inactive tab content - Gradio uses hidden attribute */
.result-tabs .tabitem[hidden] {
    display: none !important;
}

/* Markdown preview styles */
.result-tabs .markdown-preview {
    padding: 20px !important;
    line-height: 1.8 !important;
}

.result-tabs .markdown-preview img {
    display: block !important;
    margin: 16px auto !important;
    max-width: 100% !important;
    height: auto !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: var(--shadow-sm) !important;
}

.result-tabs .markdown-preview table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 16px 0 !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: var(--shadow-sm) !important;
}

.result-tabs .markdown-preview th,
.result-tabs .markdown-preview td {
    padding: 12px 16px !important;
    border: 1px solid var(--border-color) !important;
}

.result-tabs .markdown-preview th {
    background: #f8fafc !important;
    font-weight: 600 !important;
}

.result-tabs .markdown-preview tr:nth-child(even) {
    background: #f8fafc !important;
}

/* Code block styles */
.result-tabs .code-preview {
    max-height: calc(100vh - 280px) !important;
    min-height: 400px !important;
    overflow: auto !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 0.9rem !important;
    line-height: 1.6 !important;
}

/* Visualization container - vertical scroll for multi-page */
.result-tabs .vis-container {
    max-height: calc(100vh - 280px) !important;
    padding: 20px !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
}

.result-tabs .vis-container img {
    max-width: 100% !important;
    height: auto !important;
    display: block !important;
    margin: 0 auto 16px !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: var(--shadow-md) !important;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .app-title {
        font-size: 1.75rem !important;
    }
    
    .button-grid {
        grid-template-columns: repeat(2, 1fr) !important;
    }
    
    .checkbox-row {
        flex-direction: column !important;
        gap: 8px !important;
    }
}

/* Loading animation */
.loading {
    display: inline-block !important;
    width: 20px !important;
    height: 20px !important;
    border: 3px solid rgba(255,255,255,.3) !important;
    border-radius: 50% !important;
    border-top-color: white !important;
    animation: spin 1s ease-in-out infinite !important;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Scrollbar styles */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}
"""


def create_app() -> Tuple[gr.Blocks, Dict[str, Any]]:
    """Create and configure the Gradio application.
    
    Returns:
        A tuple of (demo, launch_kwargs) where launch_kwargs contains
        theme, css, and other parameters for launch() method.
    """
    
    # Gradio 6.0+: css and theme go to launch(), title stays in Blocks()
    launch_kwargs = {
        "css": CUSTOM_CSS,
        "theme": gr.themes.Soft(
            primary_hue="indigo",
            secondary_hue="cyan",
            neutral_hue="slate",
            font=["Inter", "system-ui", "sans-serif"],
        ),
    }
    
    with gr.Blocks(
        title="PaddleOCR-VL Web UI",
    ) as demo:
        
        with gr.Tabs():
            
            # ==================== Document Parsing Tab ====================
            with gr.Tab("📑 Document Parsing"):
                with gr.Row():
                    # Left column - Input
                    with gr.Column(scale=5):
                        gr.Markdown("### Upload Document")
                        file_doc = gr.File(
                            label="",
                            file_count="single",
                            type="filepath",
                            file_types=["image", ".pdf"],
                            elem_classes=["file-upload"],
                        )
                        
                        preview_doc = gr.HTML(
                            value="",
                            elem_classes=["image-preview-container"],
                            visible=False,
                        )
                        
                        gr.Markdown("*Upload a document image for full-page parsing with layout detection*")
                        
                        with gr.Row():
                            btn_parse = gr.Button(
                                "▶️ Parse Document",
                                variant="primary",
                                elem_classes=["primary"],
                                interactive=False,
                            )
                        
                        gr.Markdown("### Options")
                        with gr.Row(elem_classes=["checkbox-row"]):
                            chart_switch = gr.Checkbox(
                                label="📊 Chart Recognition",
                                value=False,
                            )
                            unwarp_switch = gr.Checkbox(
                                label="🔄 Document Unwarping",
                                value=False,
                            )
                            orient_switch = gr.Checkbox(
                                label="🧭 Orientation Detection",
                                value=False,
                            )
                    
                    # Right column - Results
                    with gr.Column(scale=7):
                        gr.Markdown("### Results")
                        with gr.Tabs(elem_classes=["result-tabs"]):
                            with gr.Tab("📝 Markdown"):
                                md_preview_doc = gr.Markdown(
                                    latex_delimiters=LATEX_DELIMITERS,
                                    elem_classes=["markdown-preview"],
                                )
                            with gr.Tab("🖼️ Visualization"):
                                vis_image_doc = gr.HTML(
                                    elem_classes=["vis-container"],
                                )
                            with gr.Tab("📋 Source"):
                                md_raw_doc = gr.Code(
                                    language="markdown",
                                    elem_classes=["code-preview"],
                                )
                
                # Event handlers
                def toggle_button(file_path):
                    """Enable button when file is uploaded, disable when cleared."""
                    return gr.update(interactive=bool(file_path))
                
                file_doc.change(
                    fn=update_preview_visibility,
                    inputs=file_doc,
                    outputs=preview_doc,
                )
                
                file_doc.change(
                    fn=toggle_button,
                    inputs=file_doc,
                    outputs=btn_parse,
                )
                
                btn_parse.click(
                    fn=handle_document_parsing,
                    inputs=[
                        file_doc,
                        chart_switch,
                        unwarp_switch,
                        orient_switch,
                    ],
                    outputs=[md_preview_doc, vis_image_doc, md_raw_doc],
                )
            
            # ==================== Element Recognition Tab ====================
            with gr.Tab("🎯 Element Recognition"):
                with gr.Row():
                    # Left column - Input
                    with gr.Column(scale=5):
                        gr.Markdown("### Upload Image")
                        file_vl = gr.File(
                            label="",
                            file_count="single",
                            type="filepath",
                            file_types=["image"],
                            elem_classes=["file-upload"],
                        )
                        
                        preview_vl = gr.HTML(
                            value="",
                            elem_classes=["image-preview-container"],
                            visible=False,
                        )
                        
                        gr.Markdown("*Upload an image element for specific recognition*")
                        
                        gr.Markdown("### Recognition Type")
                        with gr.Row(elem_classes=["button-grid"]):
                            btn_ocr = gr.Button("📝 Text", variant="secondary", interactive=False)
                            btn_formula = gr.Button("📐 Formula", variant="secondary", interactive=False)
                            btn_table = gr.Button("📊 Table", variant="secondary", interactive=False)
                            btn_chart = gr.Button("📈 Chart", variant="secondary", interactive=False)
                            btn_seal = gr.Button("🔖 Seal", variant="secondary", interactive=False)
                    
                    # Right column - Results
                    with gr.Column(scale=7):
                        gr.Markdown("### Results")
                        with gr.Tabs(elem_classes=["result-tabs"]):
                            with gr.Tab("📝 Preview"):
                                md_preview_vl = gr.Markdown(
                                    latex_delimiters=LATEX_DELIMITERS,
                                    elem_classes=["markdown-preview"],
                                )
                            with gr.Tab("📋 Raw Output"):
                                md_raw_vl = gr.Code(
                                    language="markdown",
                                    elem_classes=["code-preview"],
                                )
                
                # Event handlers
                def toggle_buttons(file_path):
                    """Enable buttons when file is uploaded, disable when cleared."""
                    has_file = bool(file_path)
                    return [gr.update(interactive=has_file) for _ in range(5)]
                
                file_vl.change(
                    fn=update_preview_visibility,
                    inputs=file_vl,
                    outputs=preview_vl,
                )
                
                recognition_buttons = [
                    btn_ocr, btn_formula, btn_table, btn_chart, btn_seal
                ]
                
                file_vl.change(
                    fn=toggle_buttons,
                    inputs=file_vl,
                    outputs=recognition_buttons,
                )
                
                # Recognition button click handlers
                recognition_mapping = [
                    (btn_ocr, "Text Recognition"),
                    (btn_formula, "Formula Recognition"),
                    (btn_table, "Table Recognition"),
                    (btn_chart, "Chart Recognition"),
                    (btn_seal, "Seal Recognition"),
                ]
                
                for btn, prompt in recognition_mapping:
                    btn.click(
                        fn=handle_targeted_recognition,
                        inputs=[file_vl, gr.State(prompt)],
                        outputs=[md_preview_vl, md_raw_vl, gr.HTML(visible=False)],
                    )
            
            # ==================== Spotting Tab ====================
            with gr.Tab("👁️ Spotting"):
                with gr.Row():
                    # Left column - Input
                    with gr.Column(scale=5):
                        gr.Markdown("### Upload Image")
                        file_spot = gr.File(
                            label="",
                            file_count="single",
                            type="filepath",
                            file_types=["image"],
                            elem_classes=["file-upload"],
                        )
                        
                        preview_spot = gr.HTML(
                            value="",
                            elem_classes=["image-preview-container"],
                            visible=False,
                        )
                        
                        gr.Markdown("*Detect and locate specific elements in the image*")
                        
                        with gr.Row():
                            btn_run_spot = gr.Button(
                                "▶️ Run Spotting",
                                variant="primary",
                                interactive=False,
                            )
                    
                    # Right column - Results
                    with gr.Column(scale=7):
                        gr.Markdown("### Results")
                        with gr.Tabs(elem_classes=["result-tabs"]):
                            with gr.Tab("🖼️ Visualization"):
                                vis_image_spot = gr.HTML(
                                    elem_classes=["vis-container"],
                                )
                            with gr.Tab("📋 JSON Result"):
                                json_spot = gr.Code(
                                    language="json",
                                    elem_classes=["code-preview"],
                                )
                
                # Event handlers
                def toggle_spot_button(file_path):
                    """Enable button when file is uploaded, disable when cleared."""
                    return gr.update(interactive=bool(file_path))
                
                file_spot.change(
                    fn=update_preview_visibility,
                    inputs=file_spot,
                    outputs=preview_spot,
                )
                
                file_spot.change(
                    fn=toggle_spot_button,
                    inputs=file_spot,
                    outputs=btn_run_spot,
                )
                
                def run_spotting_wrapper(file_path):
                    """Wrapper for spotting mode."""
                    _, json_res, vis_res = handle_targeted_recognition(
                        file_path, "Spotting"
                    )
                    return vis_res, json_res
                
                btn_run_spot.click(
                    fn=run_spotting_wrapper,
                    inputs=file_spot,
                    outputs=[vis_image_spot, json_spot],
                )

    
    return demo, launch_kwargs


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="PaddleOCR-VL Web UI")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to bind to (default: 7860)",
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public shareable link",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode to log API requests and responses",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://paddleocr.home/layout-parsing",
        help="API endpoint URL (default: http://paddleocr.home/layout-parsing)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default="",
        help="API key for authentication (optional)",
    )
    args = parser.parse_args()
    
    # Set global configuration from command line arguments
    global API_URL, API_KEY, DEBUG, HEADERS
    API_URL = args.api_url
    API_KEY = args.api_key
    DEBUG = args.debug
    
    # Update headers with API key if provided
    if API_KEY:
        HEADERS["Authorization"] = f"Bearer {API_KEY}"
    
    if DEBUG:
        print("🐛 Debug mode enabled")
    
    print(f"🚀 Starting PaddleOCR-VL Web UI...")
    print(f"   URL: http://{args.host}:{args.port}")
    print(f"   API: {API_URL}")
    
    # Create and launch the app
    app, launch_kwargs = create_app()
    
    # Add server settings to launch kwargs
    launch_kwargs.update({
        "server_name": args.host,
        "server_port": args.port,
        "share": args.share,
        "show_error": True,
    })
    
    app.launch(**launch_kwargs)


if __name__ == "__main__":
    main()
