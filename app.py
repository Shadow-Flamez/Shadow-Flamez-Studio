"""
app.py - Main Gradio Application Entry Point
"""
import sys
import time
from typing import Optional, Tuple
from PIL import Image

# Force stdout to flush immediately for Render logs
sys.stdout.flush()

import gradio as gr

# Load environment configuration first
import config
from utils import ImageUtils
from diagnostics import diagnostics, logger
from styles import STUDIO_CSS, STUDIO_HEADER_HTML, STUDIO_FOOTER_HTML
from neural_engine import neural_engine
from chroma_engine import ChromaKeyEngine
from compositor import CompositingEngine

def format_status_badge(message: str, status_type: str = "info") -> str:
    color_map = {"info": "#00ffff", "success": "#00ff66", "warning": "#ffaa00", "error": "#ff0055"}
    border_col = color_map.get(status_type, "#00ffff")
    return f'<div class="status-badge" style="border-left-color: {border_col};">STATUS: {message}</div>'

def single_image_pipeline(
    input_image: Optional[Image.Image],
    processing_mode: str,
    ai_model_name: str,
    bg_option: str,
    solid_color: str,
    progress=gr.Progress()
) -> Tuple[Optional[Image.Image], str]:
    if input_image is None:
        return None, format_status_badge("Please upload a source image first.", "warning")

    start_time = time.time()
    try:
        progress(0.3, desc=f"Executing {processing_mode}...")
        if processing_mode == "AI Neural Removal (rembg)":
            fg = neural_engine.remove_background(pil_image=input_image, model_name=ai_model_name)
        else:
            fg = ChromaKeyEngine.process_keying(
                pil_image=input_image,
                screen_type="Green Screen" if "Green" in processing_mode else "Blue Screen"
            )

        progress(0.7, desc="Applying Compositing Layer...")
        final_output = CompositingEngine.composite_layers(
            foreground=fg,
            bg_option=bg_option,
            solid_hex=solid_color
        )

        progress(1.0, desc="Rendering Complete!")
        elapsed = round(time.time() - start_time, 2)
        diagnostics.record_task("Single Image Pipeline", elapsed, details=f"Mode: {processing_mode}")
        return final_output, format_status_badge(f"Rendered in {elapsed}s | Mode: {processing_mode}", "success")
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        diagnostics.record_task("Single Image Pipeline", 0.0, status="ERROR", details=str(e))
        return None, format_status_badge(f"Error executing task: {str(e)}", "error")

def build_studio_app() -> gr.Blocks:
    with gr.Blocks(title="Shadow Flamez AI Studio Pro v5.0", css=STUDIO_CSS) as demo:
        gr.HTML(STUDIO_HEADER_HTML)

        with gr.Tabs():
            with gr.Tab("🔥 Single Image Studio"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📥 Source Input & Engine")
                        input_img = gr.Image(type="pil", label="Upload Source Image", sources=["upload", "clipboard"])
                        proc_mode = gr.Radio(
                            choices=["AI Neural Removal (rembg)", "Fast Green Screen Keying", "Fast Blue Screen Keying"],
                            value="AI Neural Removal (rembg)",
                            label="⚙️ Processing Engine"
                        )
                        ai_model_choice = gr.Dropdown(
                            choices=["u2net", "isnet-general-use", "u2netp", "silueta"],
                            value="u2net",
                            label="🧠 AI Model Selection"
                        )
                        bg_style = gr.Radio(
                            choices=["Checkerboard Preview", "Transparent (PNG)", "Solid Custom Color"],
                            value="Checkerboard Preview",
                            label="Background Mode"
                        )
                        solid_picker = gr.ColorPicker(value="#0F3460", label="Solid Color Picker")
                        btn_process = gr.Button("🔥 EXECUTE STUDIO RENDER", variant="primary", size="lg")

                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 Studio Render Result")
                        status_box = gr.HTML(format_status_badge("System Ready. Upload an image to start.", "info"))
                        output_img = gr.Image(type="pil", label="Rendered Output", format="png", interactive=False)

                btn_process.click(
                    fn=single_image_pipeline,
                    inputs=[input_img, proc_mode, ai_model_choice, bg_style, solid_picker],
                    outputs=[output_img, status_box]
                )

            with gr.Tab("📊 System Diagnostics"):
                gr.Markdown("### Real-Time Diagnostics & Performance Metrics")
                diag_html = gr.HTML(diagnostics.generate_report_html())
                btn_refresh_diag = gr.Button("🔄 REFRESH DIAGNOSTICS", variant="secondary")
                btn_refresh_diag.click(fn=lambda: diagnostics.generate_report_html(), inputs=[], outputs=[diag_html])

        gr.HTML(STUDIO_FOOTER_HTML)
    return demo

if __name__ == "__main__":
    print(f"--> Starting Gradio server on 0.0.0.0:{config.PORT}...", flush=True)
    app_demo = build_studio_app()
    app_demo.launch(
        server_name="0.0.0.0",
        server_port=config.PORT,
        show_error=True
    )
