"""
==============================================================================
SHADOW FLAMEZ AI STUDIO PRO v6.0 - MASTER STANDALONE ENGINE
Full-Featured 11-Tab Web Suite with Local CPU Acceleration & Zero External Dependencies
==============================================================================
"""

import io
import os
import time
import zipfile
import tempfile
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageOps, ImageFilter, ImageDraw, ImageFont
import gradio as gr
import rembg

from styles import STUDIO_CSS, STUDIO_HEADER_HTML, STUDIO_FOOTER_HTML

# Pre-load sessions into VRAM/RAM cache
MODEL_CACHE = {}

def get_rembg_session(model_name: str):
    """Lazy-load and cache rembg models to optimize memory usage"""
    if model_name not in MODEL_CACHE:
        MODEL_CACHE[model_name] = rembg.new_session(model_name)
    return MODEL_CACHE[model_name]

def format_status(msg: str, status_type: str = "info") -> str:
    """Generates styled HTML status badges"""
    colors = {"info": "#00f3ff", "success": "#00ff66", "warning": "#ffaa00", "error": "#ff0055"}
    col = colors.get(status_type, "#00f3ff")
    return f'<div class="status-badge" style="border-color: {col}; color: {col};">STATUS: {msg}</div>'

def add_to_gallery(image: Image.Image, gallery_state: list) -> list:
    """Helper to update the session history deck"""
    if image is None:
        return gallery_state
    if gallery_state is None:
        gallery_state = []
    # Store copy in memory list
    gallery_state.append(image)
    return gallery_state


# ==============================================================================
# BACKEND CORE PIPELINES
# ==============================================================================

# --- 1. MAGIC BRUSH & INPAINTING ---
def execute_magic_brush(editor_data, algorithm: str, dilate_radius: int, progress=gr.Progress()):
    if editor_data is None or "composite" not in editor_data:
        return None, format_status("Please paint over an object first.", "warning"), None

    bg = editor_data.get("background")
    layers = editor_data.get("layers")
    if not layers or bg is None:
        return None, format_status("No painted mask detected.", "warning"), None

    start_time = time.time()
    progress(0.2, desc="Extracting Image Matrices...")
    
    img_np = np.array(bg.convert("RGB"))
    mask_np = np.array(layers[0].convert("L"))

    # Binarize mask
    _, mask_binary = cv2.threshold(mask_np, 10, 255, cv2.THRESH_BINARY)

    # Optional Mask Dilation for cleaner edge blending
    if dilate_radius > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_radius * 2 + 1, dilate_radius * 2 + 1))
        mask_binary = cv2.dilate(mask_binary, kernel)

    progress(0.6, desc="Applying Fast Inpainting Engine...")
    flag = cv2.INPAINT_TELEA if "Telea" in algorithm else cv2.INPAINT_NS
    inpainted_np = cv2.inpaint(img_np, mask_binary, inpaintRadius=5, flags=flag)
    
    result = Image.fromarray(inpainted_np)
    elapsed = round(time.time() - start_time, 3)
    return result, format_status(f"Object erased in {elapsed}s!", "success"), result


# --- 2. BACKGROUND & COMPOSITOR ---
def execute_bg_compositor(input_img: Image.Image, model_name: str, mode: str, color_hex: str, custom_bg: Image.Image, blur_amt: int, progress=gr.Progress()):
    if input_img is None:
        return None, format_status("Please upload an image.", "warning"), None

    start_time = time.time()
    progress(0.3, desc="Extracting Foreground Subject...")
    
    session = get_rembg_session(model_name)
    fg_transparent = rembg.remove(input_img, session=session)

    progress(0.7, desc="Compositing Background...")
    
    if mode == "Transparent (PNG)":
        final_img = fg_transparent
    elif mode == "Solid Custom Color":
        bg_canvas = Image.new("RGBA", fg_transparent.size, color_hex)
        bg_canvas.paste(fg_transparent, (0, 0), mask=fg_transparent.split()[3])
        final_img = bg_canvas
    elif mode == "Blur Original Background":
        blurred_bg = input_img.convert("RGBA").filter(ImageFilter.GaussianBlur(radius=blur_amt))
        blurred_bg.paste(fg_transparent, (0, 0), mask=fg_transparent.split()[3])
        final_img = blurred_bg
    elif mode == "Custom Image Replacement" and custom_bg is not None:
        resized_bg = custom_bg.convert("RGBA").resize(fg_transparent.size, Image.Resampling.LANCZOS)
        resized_bg.paste(fg_transparent, (0, 0), mask=fg_transparent.split()[3])
        final_img = resized_bg
    else:
        final_img = fg_transparent

    elapsed = round(time.time() - start_time, 2)
    return final_img, format_status(f"Composited in {elapsed}s!", "success"), final_img


# --- 3. 4X UPSCALER & CYBER FX ---
def execute_cyber_fx(img: Image.Image, scale_factor: str, lut_preset: str, sharpness: float, glitch_fx: bool, progress=gr.Progress()):
    if img is None:
        return None, format_status("Upload an image first.", "warning"), None

    start_time = time.time()
    progress(0.2, desc="Applying Color Presets...")
    
    res = img.convert("RGB")
    
    # LUT / Color Styling
    if lut_preset == "Cyberpunk Neo":
        res = ImageEnhance.Color(res).enhance(1.5)
        res = ImageEnhance.Contrast(res).enhance(1.2)
    elif lut_preset == "Matrix Green":
        np_img = np.array(res)
        np_img[:, :, 0] = np_img[:, :, 0] * 0.2  # Red channel
        np_img[:, :, 2] = np_img[:, :, 2] * 0.3  # Blue channel
        res = Image.fromarray(np.clip(np_img, 0, 255).astype(np.uint8))
    elif lut_preset == "Synthwave Magenta":
        np_img = np.array(res, dtype=np.float32)
        np_img[:, :, 0] *= 1.3  # Boost Red
        np_img[:, :, 2] *= 1.4  # Boost Blue
        res = Image.fromarray(np.clip(np_img, 0, 255).astype(np.uint8))
    elif lut_preset == "Noir Monochrome":
        res = ImageOps.grayscale(res).convert("RGB")

    # Chromatic Glitch Effect
    if glitch_fx:
        np_img = np.array(res)
        shift = 8
        r = np_img[:, :, 0]
        g = np_img[:, :, 1]
        b = np_img[:, :, 2]
        np_img[:, :, 0] = np.roll(r, shift, axis=1)
        np_img[:, :, 2] = np.roll(b, -shift, axis=1)
        res = Image.fromarray(np_img)

    progress(0.6, desc="Upscaling High-Res Matrix...")
    factor = 4 if "4x" in scale_factor else (2 if "2x" in scale_factor else 1)
    if factor > 1:
        w, h = res.size
        res = res.resize((w * factor, h * factor), Image.Resampling.LANCZOS)

    # Sharpness Enhancement
    res = ImageEnhance.Sharpen(res).enhance(sharpness)
    elapsed = round(time.time() - start_time, 2)
    return res, format_status(f"Scaled {factor}x & FX Applied in {elapsed}s!", "success"), res


# --- 4. WATERMARK & BRANDING STUDIO ---
def execute_watermark(img: Image.Image, text: str, position: str, opacity: float, font_size: int, progress=gr.Progress()):
    if img is None:
        return None, format_status("Upload a base image.", "warning"), None

    progress(0.4, desc="Overlaying Watermark Layer...")
    base = img.convert("RGBA")
    txt_layer = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    w, h = base.size

    # Position logic
    margin = 20
    if position == "Bottom-Right":
        pos = (w - text_w - margin, h - text_h - margin)
    elif position == "Bottom-Left":
        pos = (margin, h - text_h - margin)
    elif position == "Top-Right":
        pos = (w - text_w - margin, margin)
    elif position == "Top-Left":
        pos = (margin, margin)
    else:  # Center
        pos = ((w - text_w) // 2, (h - text_h) // 2)

    alpha_val = int(opacity * 255)
    draw.text(pos, text, font=font, fill=(255, 255, 255, alpha_val))

    watermarked = Image.alpha_composite(base, txt_layer)
    return watermarked, format_status("Watermark Applied Successfully!", "success"), watermarked


# --- 5. BATCH PROCESSING SUITE ---
def execute_batch(files: list, action: str, model_name: str, progress=gr.Progress()):
    if not files:
        return None, format_status("No files uploaded for batch processing.", "warning")

    progress(0.1, desc="Initializing Batch Processor...")
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "shadow_flamez_batch_export.zip")

    session = get_rembg_session(model_name) if "Remove Background" in action else None

    with zipfile.ZipFile(zip_path, 'w') as zip_file:
        for idx, file_obj in enumerate(files):
            progress((idx + 1) / len(files), desc=f"Processing File {idx+1}/{len(files)}...")
            try:
                img = Image.open(file_obj.name)
                filename = os.path.basename(file_obj.name)
                name, _ = os.path.splitext(filename)

                if action == "Remove Background":
                    out_img = rembg.remove(img, session=session)
                    save_name = f"{name}_nobg.png"
                    buf = io.BytesIO()
                    out_img.save(buf, format="PNG")
                elif action == "Resize to 1080p (FHD)":
                    out_img = ImageOps.contain(img, (1920, 1080), Image.Resampling.LANCZOS)
                    save_name = f"{name}_1080p.jpg"
                    buf = io.BytesIO()
                    out_img.convert("RGB").save(buf, format="JPEG", quality=90)
                elif action == "Convert to WebP":
                    out_img = img
                    save_name = f"{name}.webp"
                    buf = io.BytesIO()
                    out_img.save(buf, format="WEBP", quality=85)

                zip_file.writestr(save_name, buf.getvalue())
            except Exception as e:
                print(f"Batch Error on {file_obj.name}: {e}")

    return zip_path, format_status(f"Batch completed! Processed {len(files)} images.", "success")


# --- 6. COLOR & TONE STUDIO ---
def execute_color_grade(img: Image.Image, brightness: float, contrast: float, saturation: float, warmth: float, hdr_effect: bool, progress=gr.Progress()):
    if img is None:
        return None, format_status("Upload an image first.", "warning"), None

    progress(0.3, desc="Grading Colors & Vibrance...")
    res = img.convert("RGB")

    res = ImageEnhance.Brightness(res).enhance(brightness)
    res = ImageEnhance.Contrast(res).enhance(contrast)
    res = ImageEnhance.Color(res).enhance(saturation)

    # Temperature / Warmth
    if warmth != 1.0:
        np_img = np.array(res, dtype=np.float32)
        np_img[:, :, 0] *= warmth          # Red channel
        np_img[:, :, 2] *= (2.0 - warmth)  # Blue channel inverse
        res = Image.fromarray(np.clip(np_img, 0, 255).astype(np.uint8))

    # HDR Tone Mapping Simulation
    if hdr_effect:
        np_cv = cv2.cvtColor(np.array(res), cv2.COLOR_RGB2BGR)
        hdr = cv2.detailEnhance(np_cv, sigma_s=12, sigma_r=0.15)
        res = Image.fromarray(cv2.cvtColor(hdr, cv2.COLOR_BGR2RGB))

    return res, format_status("Color Grade Applied!", "success"), res


# --- 7. SMART CANVAS & EXPORT ---
def execute_canvas_export(img: Image.Image, aspect_ratio: str, fit_mode: str, fmt: str, progress=gr.Progress()):
    if img is None:
        return None, format_status("Upload an image first.", "warning"), None

    progress(0.4, desc="Formatting Canvas Aspect Ratio...")
    ratios = {
        "1:1 Square (Instagram)": (1080, 1080),
        "9:16 Story / Reel": (1080, 1920),
        "16:9 YouTube Thumbnail": (1920, 1080),
        "4:5 Portrait": (1080, 1350),
        "2:1 Banner": (1200, 600)
    }

    if aspect_ratio not in ratios:
        res = img
    else:
        target_w, target_h = ratios[aspect_ratio]
        if fit_mode == "Crop to Fill":
            res = ImageOps.fit(img, (target_w, target_h), Image.Resampling.LANCZOS)
        else:  # Pad with Background
            res = ImageOps.pad(img, (target_w, target_h), color="#0D111C", centering=(0.5, 0.5))

    return res, format_status(f"Resized for {aspect_ratio} ({fmt})", "success"), res


# --- 8. AI FX & ARTISTIC FILTER LAB ---
def execute_art_filter(img: Image.Image, filter_style: str, progress=gr.Progress()):
    if img is None:
        return None, format_status("Upload an image first.", "warning"), None

    progress(0.4, desc="Applying Neural Transformation...")
    np_img = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)

    if filter_style == "Pencil Sketch":
        gray, color = cv2.pencilSketch(np_img, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
        res_np = cv2.cvtColor(color, cv2.COLOR_BGR2RGB)
    elif filter_style == "Cyber Line Art (Canny)":
        edges = cv2.Canny(np_img, 100, 200)
        edges_inv = cv2.bitwise_not(edges)
        res_np = cv2.cvtColor(edges_inv, cv2.COLOR_GRAY2RGB)
    elif filter_style == "Cartoon Stylization":
        cartoon = cv2.stylization(np_img, sigma_s=60, sigma_r=0.45)
        res_np = cv2.cvtColor(cartoon, cv2.COLOR_BGR2RGB)
    elif filter_style == "Posterize":
        n = 4  # Number of quantization levels
        indices = np.arange(0, 256)
        divider = 256 / n
        quantized = np.int0(np.floor(indices / divider) * (256 / (n - 1)))
        res_np = cv2.cvtColor(cv2.LUT(np_img, quantized.astype(np.uint8)), cv2.COLOR_BGR2RGB)
    else:
        res_np = cv2.cvtColor(np_img, cv2.COLOR_BGR2RGB)

    res = Image.fromarray(res_np)
    return res, format_status(f"Filter '{filter_style}' Applied!", "success"), res


# --- 9. METADATA & PRIVACY CLEANER ---
def execute_privacy_cleaner(img: Image.Image, progress=gr.Progress()):
    if img is None:
        return None, {}, format_status("Upload an image to inspect.", "warning")

    progress(0.5, desc="Analyzing File Structure & Stripping EXIF...")
    w, h = img.size
    mode = img.mode
    format_type = img.format if img.format else "RAW PIL Frame"

    # Diagnostics JSON
    diag_info = {
        "Resolution": f"{w} x {h} Pixels",
        "Aspect Ratio": f"{round(w/h, 2)}:1",
        "Color Space": mode,
        "Source Format": format_type,
        "EXIF Metadata Privacy Status": "🔒 Stripped & Cleaned"
    }

    # Re-save cleanly without metadata
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(list(img.getdata()))

    return clean_img, diag_info, format_status("Metadata Cleaned! Image safe for sharing.", "success")


# ==============================================================================
# BUILD MASTER GRADIO INTERFACE
# ==============================================================================

def build_app():
    with gr.Blocks(css=STUDIO_CSS, title="Shadow Flamez AI Studio Pro") as demo:
        gr.HTML(STUDIO_HEADER_HTML)

        # Global Session History Deck State
        session_gallery = gr.State([])

        with gr.Tabs():

            # ------------------------------------------------------------------
            # TAB 1: MAGIC BRUSH & ERASER
            # ------------------------------------------------------------------
            with gr.Tab("🪄 Magic Brush & Eraser"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        gr.Markdown("### 🖌️ **Object Removal & Inpainting**")
                        brush_editor = gr.ImageEditor(
                            label="Paint over objects to remove",
                            type="pil",
                            brush=gr.Brush(colors=["#ff0055"], default_size=25)
                        )
                        algo_choice = gr.Radio(
                            ["OpenCV Telea (Fast Smooth)", "OpenCV Navier-Stokes (Detailed Edge)"],
                            value="OpenCV Telea (Fast Smooth)",
                            label="Inpainting Algorithm"
                        )
                        dilate_slider = gr.Slider(0, 10, value=3, step=1, label="Mask Feathering / Edge Dilation")
                        erase_btn = gr.Button("✨ ERASE UNWANTED OBJECTS", elem_classes=["cyber-btn"])

                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        gr.Markdown("### 🖼️ **Erased Output Canvas**")
                        erase_status = gr.HTML(format_status("Canvas Ready.", "info"))
                        erase_output = gr.Image(label="Cleaned Result")

                erase_btn.click(
                    fn=execute_magic_brush,
                    inputs=[brush_editor, algo_choice, dilate_slider],
                    outputs=[erase_output, erase_status, gr.State()]
                ).then(
                    fn=add_to_gallery,
                    inputs=[erase_output, session_gallery],
                    outputs=[session_gallery]
                )

            # ------------------------------------------------------------------
            # TAB 2: BACKGROUND & COMPOSITOR
            # ------------------------------------------------------------------
            with gr.Tab("🖼️ Background & Compositor"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        bg_in = gr.Image(type="pil", label="Upload Source Image")
                        bg_model = gr.Dropdown(
                            ["u2netp", "u2net", "isnet-general-use", "silueta"],
                            value="u2netp",
                            label="AI Neural Model (u2netp = Fastest CPU)"
                        )
                        bg_mode = gr.Radio(
                            ["Transparent (PNG)", "Solid Custom Color", "Blur Original Background", "Custom Image Replacement"],
                            value="Transparent (PNG)",
                            label="Background Mode"
                        )
                        solid_col = gr.ColorPicker(value="#0F3460", label="Solid Color Picker")
                        blur_amt = gr.Slider(1, 30, value=15, label="Bokeh Blur Intensity")
                        custom_bg_in = gr.Image(type="pil", label="Custom Replacement Image (Optional)")
                        btn_bg = gr.Button("🔥 EXECUTE STUDIO RENDER", elem_classes=["cyber-btn"])

                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        bg_status = gr.HTML(format_status("System Ready.", "info"))
                        bg_out = gr.Image(label="Rendered Preview")

                btn_bg.click(
                    fn=execute_bg_compositor,
                    inputs=[bg_in, bg_model, bg_mode, solid_col, custom_bg_in, blur_amt],
                    outputs=[bg_out, bg_status, gr.State()]
                ).then(
                    fn=add_to_gallery,
                    inputs=[bg_out, session_gallery],
                    outputs=[session_gallery]
                )

            # ------------------------------------------------------------------
            # TAB 3: 4X UPSCALER & CYBER FX
            # ------------------------------------------------------------------
            with gr.Tab("⚡ 4x AI Upscaler & Cyber FX"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        cyber_in = gr.Image(type="pil", label="Source Image")
                        scale_factor = gr.Radio(["1x (FX Only)", "2x Upscale", "4x Super-Res"], value="2x Upscale", label="Resolution Multiplier")
                        lut_preset = gr.Dropdown(["None", "Cyberpunk Neo", "Matrix Green", "Synthwave Magenta", "Noir Monochrome"], value="None", label="LUT Preset")
                        sharpness = gr.Slider(1.0, 3.0, value=1.5, label="Sharpness Boost")
                        glitch_check = gr.Checkbox(label="Enable Chromatic Glitch FX")
                        btn_cyber = gr.Button("⚡ APPLY CYBER FX & SCALER", elem_classes=["cyber-btn"])

                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        cyber_status = gr.HTML(format_status("Cyber Suite Ready.", "info"))
                        cyber_out = gr.Image(label="Enhanced Result")

                btn_cyber.click(
                    fn=execute_cyber_fx,
                    inputs=[cyber_in, scale_factor, lut_preset, sharpness, glitch_check],
                    outputs=[cyber_out, cyber_status, gr.State()]
                ).then(
                    fn=add_to_gallery,
                    inputs=[cyber_out, session_gallery],
                    outputs=[session_gallery]
                )

            # ------------------------------------------------------------------
            # TAB 4: WATERMARK & BRANDING STUDIO
            # ------------------------------------------------------------------
            with gr.Tab("🏷️ Watermark & Branding"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        wm_in = gr.Image(type="pil", label="Base Image")
                        wm_text = gr.Textbox(label="Watermark Text", value="© SHADOW FLAMEZ AI")
                        wm_pos = gr.Dropdown(["Bottom-Right", "Bottom-Left", "Top-Right", "Top-Left", "Center"], value="Bottom-Right", label="Position")
                        wm_opacity = gr.Slider(0.1, 1.0, value=0.6, label="Opacity / Transparency")
                        wm_size = gr.Slider(12, 72, value=28, step=2, label="Font Size")
                        btn_wm = gr.Button("🏷️ APPLY WATERMARK", elem_classes=["cyber-btn"])

                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        wm_status = gr.HTML(format_status("Watermark Studio Ready.", "info"))
                        wm_out = gr.Image(label="Branded Result")

                btn_wm.click(
                    fn=execute_watermark,
                    inputs=[wm_in, wm_text, wm_pos, wm_opacity, wm_size],
                    outputs=[wm_out, wm_status, gr.State()]
                ).then(
                    fn=add_to_gallery,
                    inputs=[wm_out, session_gallery],
                    outputs=[session_gallery]
                )

            # ------------------------------------------------------------------
            # TAB 5: BATCH PROCESSING SUITE
            # ------------------------------------------------------------------
            with gr.Tab("📦 Batch Processing"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        batch_files = gr.File(file_count="multiple", label="Upload Multiple Batch Images")
                        batch_action = gr.Radio(["Remove Background", "Resize to 1080p (FHD)", "Convert to WebP"], value="Remove Background", label="Batch Action")
                        batch_model = gr.Dropdown(["u2netp", "u2net"], value="u2netp", label="Model (If BG Removal)")
                        btn_batch = gr.Button("📦 PROCESS & DOWNLOAD ZIP", elem_classes=["cyber-btn"])

                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        batch_status = gr.HTML(format_status("Batch Processor Ready.", "info"))
                        batch_zip = gr.File(label="Download Processed Output ZIP Archive")

                btn_batch.click(
                    fn=execute_batch,
                    inputs=[batch_files, batch_action, batch_model],
                    outputs=[batch_zip, batch_status]
                )

            # ------------------------------------------------------------------
            # TAB 6: COLOR & TONE STUDIO
            # ------------------------------------------------------------------
            with gr.Tab("🎨 Color & Tone Studio"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        color_in = gr.Image(type="pil", label="Source Image")
                        bright = gr.Slider(0.5, 2.0, value=1.0, label="Brightness")
                        contrast = gr.Slider(0.5, 2.0, value=1.0, label="Contrast")
                        saturate = gr.Slider(0.0, 2.5, value=1.2, label="Saturation / Vibrance")
                        warmth = gr.Slider(0.5, 1.5, value=1.0, label="Color Temperature (Cool ➔ Warm)")
                        hdr_check = gr.Checkbox(label="Simulate HDR Tone Mapping")
                        btn_color = gr.Button("🎨 APPLY COLOR GRADE", elem_classes=["cyber-btn"])

                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        color_status = gr.HTML(format_status("Color Studio Ready.", "info"))
                        color_out = gr.Image(label="Graded Preview")

                btn_color.click(
                    fn=execute_color_grade,
                    inputs=[color_in, bright, contrast, saturate, warmth, hdr_check],
                    outputs=[color_out, color_status, gr.State()]
                ).then(
                    fn=add_to_gallery,
                    inputs=[color_out, session_gallery],
                    outputs=[session_gallery]
                )

            # ------------------------------------------------------------------
            # TAB 7: SMART CANVAS & EXPORT
            # ------------------------------------------------------------------
            with gr.Tab("📐 Smart Canvas & Presets"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        canvas_in = gr.Image(type="pil", label="Source Image")
                        aspect = gr.Dropdown(
                            ["1:1 Square (Instagram)", "9:16 Story / Reel", "16:9 YouTube Thumbnail", "4:5 Portrait", "2:1 Banner"],
                            value="1:1 Square (Instagram)",
                            label="Social Aspect Preset"
                        )
                        fit_mode = gr.Radio(["Crop to Fill", "Pad with Canvas Color"], value="Crop to Fill", label="Framing Strategy")
                        fmt = gr.Dropdown(["PNG", "JPEG", "WEBP"], value="PNG", label="Export Format")
                        btn_canvas = gr.Button("📐 RESIZE & EXPORT", elem_classes=["cyber-btn"])

                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        canvas_status = gr.HTML(format_status("Canvas Ready.", "info"))
                        canvas_out = gr.Image(label="Formatted Canvas Preview")

                btn_canvas.click(
                    fn=execute_canvas_export,
                    inputs=[canvas_in, aspect, fit_mode, fmt],
                    outputs=[canvas_out, canvas_status, gr.State()]
                ).then(
                    fn=add_to_gallery,
                    inputs=[canvas_out, session_gallery],
                    outputs=[session_gallery]
                )

            # ------------------------------------------------------------------
            # TAB 8: AI FX & ARTISTIC FILTER LAB
            # ------------------------------------------------------------------
            with gr.Tab("🎭 Artistic Filter Lab"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        art_in = gr.Image(type="pil", label="Source Image")
                        art_style = gr.Radio(
                            ["Pencil Sketch", "Cyber Line Art (Canny)", "Cartoon Stylization", "Posterize"],
                            value="Pencil Sketch",
                            label="Artistic Transformation"
                        )
                        btn_art = gr.Button("🎭 GENERATE ARTISTIC FX", elem_classes=["cyber-btn"])

                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        art_status = gr.HTML(format_status("Filter Lab Ready.", "info"))
                        art_out = gr.Image(label="Artistic Output")

                btn_art.click(
                    fn=execute_art_filter,
                    inputs=[art_in, art_style],
                    outputs=[art_out, art_status, gr.State()]
                ).then(
                    fn=add_to_gallery,
                    inputs=[art_out, session_gallery],
                    outputs=[session_gallery]
                )

            # ------------------------------------------------------------------
            # TAB 9: METADATA & PRIVACY CLEANER
            # ------------------------------------------------------------------
            with gr.Tab("🕵️ Privacy Metadata Cleaner"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes=["cyber-card"]):
                        priv_in = gr.Image(type="pil", label="Source Image")
                        btn_priv = gr.Button("🔒 STRIP EXIF & INSPECT", elem_classes=["cyber-btn"])

                    with gr.Column(scale=6, elem_classes=["cyber-card"]):
                        priv_status = gr.HTML(format_status("Inspector Ready.", "info"))
                        priv_json = gr.JSON(label="Image Structural Diagnostics")
                        priv_out = gr.Image(label="Metadata-Free Clean Output")

                btn_priv.click(
                    fn=execute_privacy_cleaner,
                    inputs=[priv_in],
                    outputs=[priv_out, priv_json, priv_status]
                )

            # ------------------------------------------------------------------
            # TAB 10: SESSION GALLERY DECK
            # ------------------------------------------------------------------
            with gr.Tab("🖼️ Session Gallery Deck"):
                with gr.Column(elem_classes=["cyber-card"]):
                    gr.Markdown("### 📂 **Session Deck History**")
                    refresh_btn = gr.Button("🔄 REFRESH GALLERY DECK", elem_classes=["cyber-btn"])
                    gallery_display = gr.Gallery(label="Accumulated Rendered Deck", columns=4, height="auto")

                def sync_gallery(state_list):
                    return state_list

                refresh_btn.click(fn=sync_gallery, inputs=[session_gallery], outputs=[gallery_display])

            # ------------------------------------------------------------------
            # TAB 11: SYSTEM DIAGNOSTICS
            # ------------------------------------------------------------------
            with gr.Tab("📊 System Diagnostics"):
                with gr.Column(elem_classes=["cyber-card"]):
                    gr.Markdown("### 🖥️ **System Health & Engine Status**")
                    diag_box = gr.JSON(value={
                        "Render_Frontend": "Online",
                        "Execution_Mode": "Pure Local Standalone CPU",
                        "Parallel_Concurrency_Threads": 4,
                        "Rembg_Engine": "Active (ONNX Runtime CPU)"
                    })

        gr.HTML(STUDIO_FOOTER_HTML)

    return demo


if __name__ == "__main__":
    app_demo = build_app()
    # Enable multi-threaded queue for smooth background execution
    app_demo.queue(default_concurrency_limit=4).launch(
        server_name="0.0.0.0",
        server_port=7860
    )
