"""API client for PaddleOCR service."""

import json
import re
from typing import Any, Dict, Tuple

import requests

from paddleocr_ui.config import Settings
from paddleocr_ui.utils import escape_inequalities_in_math, file_to_base64, process_base64_image


def call_api(
    path_or_url: str,
    use_layout_detection: bool,
    prompt_label: str | None = None,
    use_chart_recognition: bool = False,
    use_doc_unwarping: bool = True,
    use_doc_orientation_classify: bool = True,
    settings: Settings | None = None,
) -> Dict[str, Any]:
    """Call the PaddleOCR API with the given parameters."""
    if settings is None:
        settings = Settings()
    
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
    if settings.debug:
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
        print(f"Sending API request to {settings.api_url}...")
        resp = requests.post(
            settings.api_url,
            json=payload,
            headers=settings.get_headers(),
            timeout=120
        )
        resp.raise_for_status()
        data = resp.json()
        
        # Debug: dump response
        if settings.debug:
            print("-" * 60)
            print("DEBUG: API Response")
            print("-" * 60)
            # Truncate base64 image data in response for readability
            log_data = json.dumps(data, ensure_ascii=False)
            # Find and truncate base64 strings in response
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
        raise RuntimeError(f"API request failed: {e}") from e

    if data.get("errorCode", -1) != 0:
        error_msg = data.get("errorMsg", "Unknown error")
        raise RuntimeError(f"API error: {error_msg}")

    return data


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
