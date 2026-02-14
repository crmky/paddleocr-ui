"""Business logic handlers for Gradio callbacks."""

import json
from typing import Tuple

import gradio as gr

from paddleocr_ui.api import call_api, process_api_response
from paddleocr_ui.config import Settings


def handle_document_parsing(
    path_or_url: str,
    use_chart_recognition: bool,
    use_doc_unwarping: bool,
    use_doc_orientation_classify: bool,
    settings: Settings | None = None,
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
        settings=settings,
    )
    result = data.get("result", {})
    return process_api_response(result)


def handle_targeted_recognition(
    path_or_url: str,
    prompt_choice: str,
    settings: Settings | None = None,
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
        settings=settings,
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
                    from paddleocr_ui.utils import process_base64_image
                    img_src = process_base64_image(img_data)
                    vis_html = f'<img src="{img_src}" alt="Spotting Visualization" loading="lazy">'

        return md_preview, md_raw, vis_html

    return md_preview, md_raw, vis_html
