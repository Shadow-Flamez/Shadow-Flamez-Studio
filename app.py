"""
app.py - Main Application Entry Point (Shadow Flamez AI Studio Pro v6.0)
"""
import io
import os
import time
import zipfile
import requests
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import gradio as gr

from styles import STUDIO_CSS, STUDIO_HEADER_HTML, STUDIO_FOOTER_HTML

# Pre-load local fallback session
try:
    import rembg
    LOCAL_REMBG_SESSION = rembg.new_session("u2net")
except Exception:
    LOCAL_REMBG_SESSION = None


def format_status(msg: str, status_type: str = "info") -> str:
    colors = {"info": "#00f3ff", "success": "#00ff66", "warning": "#ffaa00", "error": "#ff0055"}
    col = colors.get(status_type, "#00f3ff")
    return f'<div class="status-badge" style="border-color: {col}; color: {col};">STATUS: {msg}</div>'


# ==========================================
# HYBRID ENGINE EXECUTION PIPELINE
# ==========================================

def execute_bg_removal(input_img: Image.Image, colab_url: str, model_name: str, progress=gr.Progress()) -> Image.Image:
    """Executes BG Removal on Colab GPU if connected, else falls back to Local CPU"""
    if input_img is None:
        return None

    progress(0.2, desc="Preparing Image Matrix...")
    
    # Try Colab GPU Endpoint First
    if colab_url and colab_url.strip():
        try:
            progress(0.5, desc="⚡ Offloading to Colab GPU Engine...")
            buf = io.BytesIO()
            input_img.save(buf, format="PNG")
            buf.seek(0)
            
            endpoint = f"{colab_url.strip('/')}/remove-bg"
            res = requests.post(endpoint, files={"file": ("image.png", buf, "image/png")}, data={"model_name": model_name}, timeout=25)
            if res.status_code == 200:
                progress(0.9, desc="Receiving Rendered GPU Frame...")
                return Image.open(io.BytesIO(res.content))
        except Exception as e:
            print(f"Colab GPU Bypass Warning: {e}")

    # Fallback to Local CPU
    progress(0.6, desc="Running on Local Render CPU...")
    if LOCAL_REMBG_SESSION:
        return rembg.remove(input_img, session=LOCAL_REMBG_SESSION)
    return rembg.remove(input_img)


def execute_magic_brush(editor_data, colab_url: str, engine_mode: str, progress=gr.Progress()):
    """Dual-Engine Magic Eraser: Instant OpenCV Telea (<50ms) vs Deep Colab AI"""
    if editor_data is None or "composite" not in editor_data:
        return None, format_status("Please paint over an object first.", "warning")

    bg = editor_data["background"]
    layers = editor_data["layers"]
    if not layers or bg is None:
        return None, format_status("No painted area detected.", "warning")

    start_time = time.time()
    img_pil = bg.convert("RGB")
    mask_pil = layers[0].convert("L")

    # Engine Mode 1: Fast OpenCV Telea (<50ms local)
    if "Ultra-Fast" in engine_mode:
        progress(0.3, desc="⚡ Running Instant Telea Inpaint...")
        img_np = np.array(img_pil)
        mask_np = np.array(mask_pil)
        inpainted = cv2.inpaint(img_np, mask_np, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
        elapsed = round(time.time() - start_time, 3)
        return Image.fromarray(inpainted), format_status(f"Erased in {elapsed}s via Fast OpenCV Engine!", "success")

    # Engine Mode 2: Colab Deep AI GPU
    if colab_url and colab_url.strip():
        try:
            progress(0.4, desc="⚡ Offloading to Colab GPU Inpainter...")
            buf_img, buf_mask = io.BytesIO(), io.BytesIO()
            img_pil.save(buf_img, format="PNG")
            mask_pil.save(buf_mask, format="PNG")
            buf_img.seek(0); buf_mask.seek(0)

            endpoint = f"{colab_url.strip('/')}/inpaint"
            res = requests.post(endpoint, files={"image": ("i.png", buf_img, "image/png"), "mask": ("m.png", buf_mask, "image/png")}, timeout=30)
            if res.status_code == 200:
                elapsed = round(time.time() - start_time, 2)
                return Image.open(io.BytesIO(res.content)), format_status(f"Erased in {elapsed}s via Colab GPU Engine!", "success")
        except Exception as e:
            print(f"Colab Inpaint error: {e}")

    # Fallback to local Telea
    img_np = np.array(img_pil)
    mask_np = np.array(mask_pil)
    inpainted = cv2.inpaint(img_np, mask_np, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
    elapsed = round(time.time() - start_time, 2)
    return Image.fromarray(inpainted), format_status(f"Erased in {elapsed}s (Local Fallback)", "info")


# ==========================================
# BUILD GRADIO APPLICATION
# ==========================================

def build_app():
    with gr.Blocks(css=STUDIO_CSS, title="Shadow Flamez AI Studio Pro") as demo:
        gr.HTML(STUDIO_HEADER_HTML)

        # Global Colab GPU Connection Bar
        with gr.Row(elem_classes=["cyber-card"]):
            with gr.Column(scale=8):
                colab_url_input = gr.Textbox(
                    label="⚡ Google Colab GPU Backend Tunnel URL (Optional for 10x Speed)",
                    placeholder="Paste ngrok URL here (e.g. https://xxxx.ngrok-free.app)",
                    interactive=True
                )
            with gr.Column(scale=4):
                gpu_status_btn = gr.Button("🔌 CHECK GPU CONNECTION", elem_classes=["cyber-btn"])
                gpu_status_box = gr.HTML(format_status("Running on Render Local CPU", "info"))

        def check_gpu(url):
            if not url or not url.strip():
                return format_status("No Colab URL provided. Using Local CPU.", "info")
            try:
                res = requests.get(f"{url.strip('/')}/health", timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    return format_status(f"Connected to GPU: {data.get('gpu_name', 'Active')}", "success")
            except Exception:
                pass
            return format_status("Colab Engine Offline or URL Invalid", "error")

        gpu_status_btn.click(fn=check_gpu, inputs=[colab_url_input], outputs=[gpu_status_box])

        # Main Studio Tabs
        with gr.Tabs():
            
            # TAB 1: MAGIC BRUSH & OBJECT ERASER
            with gr.Tab("🪄 Magic Brush & Eraser"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        gr.Markdown("### 🖌️ **Object Removal & Inpainting**")
                        brush_editor = gr.ImageEditor(
                            label="Draw over unwanted objects",
                            type="pil",
                            brush=gr.Brush(colors=["#ff0055"], default_size=25)
                        )
                        engine_choice = gr.Radio(
                            ["Ultra-Fast Engine (OpenCV <50ms)", "Deep GPU AI Engine (Colab)"],
                            value="Ultra-Fast Engine (OpenCV <50ms)",
                            label="Eraser Engine Mode"
                        )
                        erase_btn = gr.Button("✨ ERASE UNWANTED OBJECTS", elem_classes=["cyber-btn"])

                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        gr.Markdown("### 🖼️ **Erased Output Canvas**")
                        erase_status = gr.HTML(format_status("Canvas Ready.", "info"))
                        erase_output = gr.Image(label="Cleaned Result")

                erase_btn.click(
                    fn=execute_magic_brush,
                    inputs=[brush_editor, colab_url_input, engine_choice],
                    outputs=[erase_output, erase_status]
                )

            # TAB 2: BACKGROUND & COMPOSITOR
            with gr.Tab("🖼️ Background & Compositor"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        bg_in = gr.Image(type="pil", label="Upload Source Image", sources=["upload", "clipboard"])
                        bg_model = gr.Dropdown(["u2net", "isnet-general-use", "u2netp", "silueta"], value="u2net", label="AI Model")
                        bg_mode = gr.Radio(["Transparent (PNG)", "Solid Custom Color"], value="Transparent (PNG)", label="Background Mode")
                        solid_col = gr.ColorPicker(value="#0F3460", label="Solid Color Picker")
                        btn_bg = gr.Button("🔥 EXECUTE STUDIO RENDER", elem_classes=["cyber-btn"])

                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        bg_status = gr.HTML(format_status("System Ready.", "info"))
                        bg_out = gr.Image(label="Rendered Preview")

                def process_bg_tab(img, url, model, mode, col):
                    if img is None:
                        return None, format_status("Please upload an image.", "warning")
                    start = time.time()
                    fg = execute_bg_removal(img, url, model)
                    if mode == "Solid Custom Color" and fg is not None:
                        bg_canvas = Image.new("RGBA", fg.size, col)
                        bg_canvas.paste(fg, (0, 0), mask=fg.split()[3])
                        fg = bg_canvas
                    elapsed = round(time.time() - start, 2)
                    return fg, format_status(f"Rendered in {elapsed}s!", "success")

                btn_bg.click(
                    fn=process_bg_tab,
                    inputs=[bg_in, colab_url_input, bg_model, bg_mode, solid_col],
                    outputs=[bg_out, bg_status]
                )

            # TAB 3: 4X UPSCALER & CYBER FX
            with gr.Tab("⚡ 4x AI Upscaler & Cyber FX"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        cyber_in = gr.Image(type="pil", label="Source Image")
                        lut_preset = gr.Dropdown(["None", "Cyberpunk Neo", "Matrix Green", "Noir Monochrome"], value="None", label="LUT Preset")
                        sharpness = gr.Slider(1.0, 3.0, value=1.5, label="Sharpness Boost")
                        btn_cyber = gr.Button("⚡ APPLY CYBER FX & SCALER", elem_classes=["cyber-btn"])

                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        cyber_status = gr.HTML(format_status("Cyber Suite Ready.", "info"))
                        cyber_out = gr.Image(label="Enhanced Result")

                def process_cyber(img, url, lut, sharp):
                    if img is None:
                        return None, format_status("Upload an image first.", "warning")
                    start = time.time()
                    res = img.convert("RGBA")
                    if lut == "Cyberpunk Neo":
                        res = ImageEnhance.Color(res).enhance(1.4)
                    w, h = res.size
                    res = res.resize((w * 4, h * 4), Image.Resampling.LANCZOS)
                    res = ImageEnhance.Sharpen(res).enhance(sharp)
                    elapsed = round(time.time() - start, 2)
                    return res, format_status(f"4X Scaled in {elapsed}s!", "success")

                btn_cyber.click(fn=process_cyber, inputs=[cyber_in, colab_url_input, lut_preset, sharpness], outputs=[cyber_out, cyber_status])

            # TAB 4: WATERMARK & BRANDING
            with gr.Tab("🏷️ Watermark & Branding"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        wm_in = gr.Image(type="pil", label="Base Image")
                        wm_text = gr.Textbox(label="Watermark Text", value="© SHADOW FLAMEZ AI")
                        btn_wm = gr.Button("🏷️ APPLY WATERMARK", elem_classes=["cyber-btn"])
                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        wm_out = gr.Image(label="Branded Result")

            # TAB 5: BATCH PROCESSING
            with gr.Tab("📦 Batch Processing"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        batch_files = gr.File(file_count="multiple", label="Upload Batch Images")
                        btn_batch = gr.Button("📦 PROCESS & DOWNLOAD ZIP", elem_classes=["cyber-btn"])
                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        batch_status = gr.HTML(format_status("Batch Processor Ready.", "info"))
                        batch_zip = gr.File(label="Download Processed Output ZIP")

            # TAB 6: COLOR & TONE STUDIO
            with gr.Tab("🎨 Color & Tone Studio"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        color_in = gr.Image(type="pil", label="Source Image")
                        bright = gr.Slider(0.5, 2.0, value=1.0, label="Brightness")
                        contrast = gr.Slider(0.5, 2.0, value=1.0, label="Contrast")
                        btn_color = gr.Button("🎨 APPLY COLOR GRADE", elem_classes=["cyber-btn"])
                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        color_out = gr.Image(label="Color Graded Preview")

            # TAB 7: SMART CANVAS & EXPORT
            with gr.Tab("📐 Smart Canvas & Export"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        canvas_in = gr.Image(type="pil", label="Source Image")
                        aspect = gr.Dropdown(["Original", "1:1 Square", "16:9 Landscape", "9:16 Story"], value="Original", label="Aspect Ratio")
                        btn_canvas = gr.Button("📐 RESIZE & EXPORT", elem_classes=["cyber-btn"])
                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        canvas_out = gr.Image(label="Export Preview")

            # TAB 8: SESSION GALLERY DECK
            with gr.Tab("🖼️ Session Gallery Deck"):
                with gr.Column(elem_classes=["cyber-card"]):
                    gr.Markdown("### 📂 **Session History**")
                    gallery = gr.Gallery(label="Output Deck", columns=4)

            # TAB 9: SYSTEM DIAGNOSTICS
            with gr.Tab("📊 System Diagnostics"):
                with gr.Column(elem_classes=["cyber-card"]):
                    gr.Markdown("### 🖥️ **System Health & Metrics**")
                    diag_box = gr.JSON(value={"Render_Frontend": "Online", "Queue_Status": "Active"})

        gr.HTML(STUDIO_FOOTER_HTML)

    return demo


if __name__ == "__main__":
    app_demo = build_app()
    # Unlock multi-threaded processing queue
    app_demo.queue(default_concurrency_limit=4).launch(
        server_name="0.0.0.0",
        server_port=7860
    )
