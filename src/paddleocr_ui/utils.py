"""Utility functions for image processing and data conversion."""

import base64
import os
import re
from typing import Tuple
from urllib.parse import urlparse

import requests


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
