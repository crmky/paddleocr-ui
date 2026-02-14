"""Gradio UI definition for PaddleOCR-VL Web UI."""

from typing import Any, Dict, Tuple

import gradio as gr

from paddleocr_ui.config import Settings
from paddleocr_ui.handlers import handle_document_parsing, handle_targeted_recognition
from paddleocr_ui.utils import render_image_preview

# LaTeX delimiters for formula rendering
LATEX_DELIMITERS = [
    {"left": "$$", "right": "$$", "display": True},
    {"left": "$", "right": "$", "display": False},
    {"left": "\\(", "right": "\\)", "display": False},
    {"left": "\\[", "right": "\\]", "display": True},
]

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


def update_preview_visibility(path_or_url: str | None) -> Dict:
    """Update preview visibility based on input."""
    if path_or_url:
        html_content = render_image_preview(path_or_url)
        return gr.update(value=html_content, visible=True)
    else:
        return gr.update(value="", visible=False)


def create_app(settings: Settings | None = None) -> Tuple[gr.Blocks, Dict[str, Any]]:
    """Create and configure the Gradio application.
    
    Args:
        settings: Application settings. If None, uses default settings.
        
    Returns:
        A tuple of (demo, launch_kwargs) where launch_kwargs contains
        theme, css, and other parameters for launch() method.
    """
    if settings is None:
        settings = Settings()
    
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
                
                def handle_doc_wrapper(path, chart, unwarp, orient):
                    return handle_document_parsing(path, chart, unwarp, orient, settings)
                
                btn_parse.click(
                    fn=handle_doc_wrapper,
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
                        # Hidden component for visualization output (3rd return value)
                        vis_hidden_vl = gr.HTML(visible=False)
                
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
                
                def handle_vl_wrapper(path, prompt):
                    return handle_targeted_recognition(path, prompt, settings)
                
                for btn, prompt in recognition_mapping:
                    btn.click(
                        fn=handle_vl_wrapper,
                        inputs=[file_vl, gr.State(prompt)],
                        outputs=[md_preview_vl, md_raw_vl, vis_hidden_vl],
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
                        file_path, "Spotting", settings
                    )
                    return vis_res, json_res
                
                btn_run_spot.click(
                    fn=run_spotting_wrapper,
                    inputs=file_spot,
                    outputs=[vis_image_spot, json_spot],
                )

    
    return demo, launch_kwargs
