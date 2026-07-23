"""
app.py - Main Gradio Application Entry Point (Shadow Flamez AI Studio Pro v5.5)
"""
import sys
import traceback
import time
import io
import os
import zipfile
from typing import Optional, Tuple
from PIL import Image

print("--> Launching Shadow Flamez AI Studio Engine...", flush=True)

try:
    import config
    from utils import ImageUtils
    from diagnostics import diagnostics, logger
    from styles import STUDIO_CSS, STUDIO_HEADER_HTML, STUDIO_FOOTER_HTML
    from neural_engine import neural_engine
    from chroma_engine import ChromaKeyEngine
    from compositor import CompositingEngine

    import gradio as gr
    print("--> All Engine Modules Loaded Successfully!", flush=True)

except Exception as err:
    print(f"\n❌ STARTUP ERROR:\n{err}", flush=True)
    traceback.print_exc()
    sys.exit(1)


def format_status_badge(message: str, status_type: str = "info") -> str:
    color_map = {"info": "#00ffff", "success": "#00ff66", "warning": "#ffaa00", "error": "#ff0055"}
    border_col = color_map.get(status_type, "#00ffff")
    return f'<div class="status-badge" style="border-left-color: {border_col};">STATUS: {message}</div>'


# Pipeline Functions
def single_image_pipeline(
    input_image: Optional[Image.Image],
    processing_mode: str,
    ai_model_name: str,
    bg_option: str,
    solid_color: str,
    enable_shadow: bool,
    shadow_x: int,
    shadow_y: int,
    shadow_blur: int,
    shadow_color: str,
    enable_aura: bool,
    aura_color: str,
    aura_radius: int,
    progress=gr.Progress(track_tqdm=True)
) -> Tuple[Optional[Image.Image], str]:
    if input_image is None:
        return None, format_status_badge("Please upload a source image first.", "warning")

    start_time = time.time()
    try:
        progress(0.2, desc="Rescaling for optimal processing speed...")
        proc_img = ImageUtils.resize_for_performance(input_image, max_dim=2048)

        progress(0.4, desc=f"Executing {processing_mode}...")
        if "AI Neural" in processing_mode:
            fg = neural_engine.remove_background(pil_image=proc_img, model_name=ai_model_name)
        else:
            fg = ChromaKeyEngine.process_keying(
                pil_image=proc_img,
                screen_type="Green Screen" if "Green" in processing_mode else "Blue Screen"
            )

        # Drop Shadow Application
        if enable_shadow:
            progress(0.6, desc="Rendering Realistic Drop Shadow...")
            fg = neural_engine.apply_drop_shadow(
                fg, offset_x=int(shadow_x), offset_y=int(shadow_y),
                blur_r=int(shadow_blur), shadow_hex=shadow_color
            )

        # Neon Aura Application
        if enable_aura:
            progress(0.7, desc="Generating Neon Halo Backglow...")
            fg = neural_engine.generate_neon_aura(
                fg, aura_color_hex=aura_color, blur_radius=int(aura_radius)
            )

        progress(0.85, desc="Applying Compositing Layer...")
        final_output = CompositingEngine.composite_layers(
            foreground=fg,
            bg_option=bg_option,
            solid_hex=solid_color
        )

        progress(1.0, desc="Rendering Complete!")
        elapsed = round(time.time() - start_time, 2)
        diagnostics.record_task("Single Image Studio", elapsed, details=f"Mode: {processing_mode}")
        return final_output, format_status_badge(f"Rendered in {elapsed}s | Engine: {processing_mode}", "success")
    
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        diagnostics.record_task("Single Image Studio", 0.0, status="ERROR", details=str(e))
        return None, format_status_badge(f"Error executing task: {str(e)}", "error")


def process_cyber_suite(input_img, upscale_on, sharpness, outline_on, outline_col, stroke_w, glitch_on, glitch_offset, lut_preset, pixel_on, pixel_size):
    if input_img is None:
        return None, format_status_badge("Upload an image for Cyber FX processing.", "warning")

    start = time.time()
    try:
        res = ImageUtils.ensure_rgba(input_img)

        if lut_preset != "None":
            res = neural_engine.apply_lut_preset(res, preset=lut_preset)

        if glitch_on:
            res = neural_engine.apply_rgb_glitch(res, offset=int(glitch_offset))

        if outline_on:
            res = neural_engine.generate_cyber_outline(res, outline_hex=outline_col, stroke_width=int(stroke_w))

        if pixel_on:
            res = neural_engine.pixel_art_downscale(res, pixel_size=int(pixel_size))

        if upscale_on:
            res = neural_engine.upscale_4x_neural(res, sharpness_boost=sharpness)

        elapsed = round(time.time() - start, 2)
        diagnostics.record_task("Cyber FX Suite", elapsed)
        return res, format_status_badge(f"Cyber Suite rendered in {elapsed}s!", "success")
    except Exception as e:
        return None, format_status_badge(f"Cyber FX Error: {str(e)}", "error")


def process_batch_zip(files, mode, ai_model):
    if not files:
        return None, format_status_badge("No image files uploaded for batch processing.", "warning")

    start = time.time()
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, file_path in enumerate(files):
            img = Image.open(file_path)
            if "AI Neural" in mode:
                res = neural_engine.remove_background(img, model_name=ai_model)
            else:
                res = ChromaKeyEngine.process_keying(img, screen_type="Green Screen" if "Green" in mode else "Blue Screen")
            
            img_bytes = io.BytesIO()
            res.save(img_bytes, format="PNG")
            zip_file.writestr(f"studio_extracted_{idx + 1}.png", img_bytes.getvalue())

    zip_buffer.seek(0)
    temp_zip_path = "/tmp/batch_extracted.zip" if os.name != "nt" else "batch_extracted.zip"
    with open(temp_zip_path, "wb") as f:
        f.write(zip_buffer.getvalue())

    elapsed = round(time.time() - start, 2)
    diagnostics.record_task("Batch ZIP Pipeline", elapsed, details=f"Processed {len(files)} items")
    return temp_zip_path, format_status_badge(f"Successfully processed {len(files)} images in {elapsed}s!", "success")


# UI Construction
def build_studio_app() -> gr.Blocks:
    with gr.Blocks(title="Shadow Flamez AI Studio Pro v5.5", css=STUDIO_CSS) as demo:
        gr.HTML(STUDIO_HEADER_HTML)

        with gr.Tabs():
            # TAB 1: MAIN SINGLE IMAGE STUDIO
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

                        with gr.Accordion("🌑 Drop Shadow FX (Optional)", open=False):
                            shadow_on = gr.Checkbox(label="Enable Realistic Drop Shadow", value=False)
                            shadow_x = gr.Slider(-50, 50, value=15, label="Offset X")
                            shadow_y = gr.Slider(-50, 50, value=20, label="Offset Y")
                            shadow_blur = gr.Slider(0, 40, value=15, label="Shadow Blur Radius")
                            shadow_col = gr.ColorPicker(value="#000000", label="Shadow Color")

                        with gr.Accordion("✨ Neon Backglow Halo (Optional)", open=False):
                            aura_on = gr.Checkbox(label="Enable Neon Aura Glow", value=False)
                            aura_col = gr.ColorPicker(value="#00FFFF", label="Aura Glow Color")
                            aura_rad = gr.Slider(5, 50, value=20, label="Glow Radius")

                        btn_process = gr.Button("🔥 EXECUTE STUDIO RENDER", elem_classes=["cyber-button"], size="lg")

                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 Studio Render Result")
                        status_box = gr.HTML(format_status_badge("System Ready. Upload an image to start.", "info"))
                        output_img = gr.Image(type="pil", label="Rendered Output", format="png", interactive=False)

                btn_process.click(
                    fn=single_image_pipeline,
                    inputs=[
                        input_img, proc_mode, ai_model_choice, bg_style, solid_picker,
                        shadow_on, shadow_x, shadow_y, shadow_blur, shadow_col,
                        aura_on, aura_col, aura_rad
                    ],
                    outputs=[output_img, status_box]
                )

            # TAB 2: CYBER GRAPHICS & 4X SCALER
            with gr.Tab("⚡ 4X Scaler & Cyber FX"):
                with gr.Row():
                    with gr.Column(scale=1):
                        cyber_in = gr.Image(type="pil", label="Source Image", sources=["upload", "clipboard"])
                        
                        gr.Markdown("#### 🎨 Cinematic Color Grade Presets")
                        lut_preset = gr.Dropdown(["None", "Cyberpunk Neo", "Matrix Green", "Golden Hour", "Noir Monochrome"], value="None", label="LUT Preset")
                        
                        gr.Markdown("#### 👾 Retro Glitch & Pixel Art")
                        glitch_on = gr.Checkbox(label="Enable RGB Glitch Split", value=False)
                        glitch_offset = gr.Slider(1, 30, value=10, label="Glitch Shift")
                        pixel_on = gr.Checkbox(label="Enable 8-Bit Pixel Art Effect", value=False)
                        pixel_size = gr.Slider(2, 32, value=12, label="Pixel Size")

                        gr.Markdown("#### ⚡ Cyber Contour & 4X Resolution")
                        outline_on = gr.Checkbox(label="Enable Cyber Outline Contouring", value=False)
                        outline_col = gr.ColorPicker(value="#FF007F", label="Outline Color")
                        stroke_w = gr.Slider(1, 15, value=4, label="Stroke Width")
                        upscale_on = gr.Checkbox(label="Enable AI 4X Super Resolution Scaler", value=True)
                        sharp = gr.Slider(1.0, 3.0, value=1.5, step=0.1, label="Sharpening Intensity")

                        btn_cyber = gr.Button("⚡ APPLY CYBER FX & SCALER", elem_classes=["cyber-button"])

                    with gr.Column(scale=1):
                        cyber_status = gr.HTML(format_status_badge("Cyber Suite Ready.", "info"))
                        cyber_out = gr.Image(type="pil", label="Enhanced Result", format="png")

                btn_cyber.click(
                    fn=process_cyber_suite,
                    inputs=[cyber_in, upscale_on, sharp, outline_on, outline_col, stroke_w, glitch_on, glitch_offset, lut_preset, pixel_on, pixel_size],
                    outputs=[cyber_out, cyber_status]
                )

            # TAB 3: BATCH PROCESSING
            with gr.Tab("📦 Batch ZIP Exporter"):
                with gr.Row():
                    with gr.Column(scale=1):
                        batch_files = gr.File(file_count="multiple", label="Upload Multiple Batch Images")
                        b_mode = gr.Radio(["AI Neural Removal (rembg)", "Fast Green Screen Keying", "Fast Blue Screen Keying"], value="AI Neural Removal (rembg)", label="Processing Engine")
                        b_model = gr.Dropdown(["u2net", "isnet-general-use", "u2netp", "silueta"], value="u2net", label="AI Model")
                        btn_batch = gr.Button("📦 PROCESS & DOWNLOAD ZIP", elem_classes=["cyber-button"])

                    with gr.Column(scale=1):
                        b_status = gr.HTML(format_status_badge("Batch Processor Ready.", "info"))
                        b_zip = gr.File(label="Download Processed Output ZIP")

                btn_batch.click(
                    fn=process_batch_zip,
                    inputs=[batch_files, b_mode, b_model],
                    outputs=[b_zip, b_status]
                )

            # TAB 4: SYSTEM DIAGNOSTICS
            with gr.Tab("📊 System Diagnostics"):
                gr.Markdown("### Real-Time Diagnostics & Performance Metrics")
                diag_html = gr.HTML(diagnostics.generate_report_html())
                btn_refresh_diag = gr.Button("🔄 REFRESH DIAGNOSTICS")
                btn_refresh_diag.click(fn=lambda: diagnostics.generate_report_html(), inputs=[], outputs=[diag_html])

        gr.HTML(STUDIO_FOOTER_HTML)
    return demo


if __name__ == "__main__":
    app_demo = build_studio_app()
    app_demo.queue().launch(
        server_name="0.0.0.0",
        server_port=config.PORT,
        share=False
    )
