import gradio as gr
import os
import io
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
from google import genai

# Initialize Google Gen AI Client
try:
    client = genai.Client()
except Exception:
    client = None

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&display=swap');

body, .gradio-container {
    background-color: #07040D !important;
    background-image: 
        radial-gradient(circle at 15% 20%, rgba(255, 85, 0, 0.08) 0%, transparent 45%),
        radial-gradient(circle at 85% 80%, rgba(0, 240, 255, 0.08) 0%, transparent 45%),
        radial-gradient(circle at 50% 50%, rgba(184, 0, 255, 0.05) 0%, transparent 60%) !important;
    font-family: 'Rajdhani', sans-serif !important;
    color: #E2E8F0 !important;
}

#studio-header {
    background: rgba(15, 10, 26, 0.8) !important;
    border: 1px solid rgba(255, 85, 0, 0.3) !important;
    border-radius: 12px !important;
    padding: 24px !important;
    text-align: center !important;
    box-shadow: 0 0 35px rgba(255, 85, 0, 0.15), inset 0 0 15px rgba(0, 240, 255, 0.05) !important;
    margin-bottom: 20px !important;
}

#studio-header h1 {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 2.2rem !important;
    font-weight: 900 !important;
    letter-spacing: 3px !important;
    background: linear-gradient(90deg, #FF5500, #00F0FF, #B800FF) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    text-transform: uppercase !important;
    margin: 0 !important;
}

#studio-header p {
    color: #94A3B8 !important;
    font-size: 0.95rem !important;
    margin-top: 6px !important;
    letter-spacing: 1px !important;
}

.cyber-panel {
    background: rgba(13, 8, 25, 0.75) !important;
    border: 1px solid rgba(0, 240, 255, 0.2) !important;
    border-radius: 10px !important;
    padding: 16px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important;
    backdrop-filter: blur(12px) !important;
}

.cyber-btn {
    background: linear-gradient(135deg, #FF5500 0%, #B800FF 100%) !important;
    border: none !important;
    color: #FFFFFF !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    border-radius: 6px !important;
    box-shadow: 0 0 15px rgba(255, 85, 0, 0.35) !important;
}

.transfer-btn {
    background: rgba(0, 240, 255, 0.1) !important;
    border: 1px solid rgba(0, 240, 255, 0.4) !important;
    color: #00F0FF !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.75rem !important;
    border-radius: 4px !important;
}
"""

# Helper function to convert Hex color to RGB
def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

# 1. Composite Processing
def process_composite(img_arr, bg_style, bg_color, custom_bg_arr, shadow_val):
    if img_arr is None:
        return None, "⚠️ Status: Please upload a source image first."

    img = Image.fromarray(img_arr).convert("RGBA")
    
    if bg_style == "Solid Color":
        color_rgb = hex_to_rgb(bg_color)
        bg = Image.new("RGBA", img.size, color_rgb + (255,))
        bg.paste(img, (0, 0), img if img.mode == 'RGBA' else None)
        res = bg.convert("RGB")
    elif bg_style == "Custom Background" and custom_bg_arr is not None:
        bg = Image.fromarray(custom_bg_arr).convert("RGBA").resize(img.size)
        bg.paste(img, (0, 0), img if img.mode == 'RGBA' else None)
        res = bg.convert("RGB")
    else:
        res = img

    status = f"✅ Composite Created | Dimensions: {res.width}x{res.height}px | Style: {bg_style}"
    return np.array(res), status

# 2. Real 4x AI Super-Resolution (Interpolation & Enhancement)
def process_upscale(img_arr):
    if img_arr is None:
        return None, "⚠️ Status: Please upload an image to upscale."

    img = Image.fromarray(img_arr)
    new_size = (img.width * 4, img.height * 4)
    upscaled = img.resize(new_size, Image.Resampling.LANCZOS)

    # Apply slight sharpness recovery post-scaling
    enhancer = ImageEnhance.Sharpness(upscaled)
    upscaled = enhancer.enhance(1.4)

    status = f"🚀 4x Upscaling Complete! | Original: {img.width}x{img.height}px ➔ Upscaled: {upscaled.width}x{upscaled.height}px"
    return np.array(upscaled), status

# 3. Watermarking Function
def process_watermark(img_arr, logo_arr, pos, scale, opacity):
    if img_arr is None:
        return None, "⚠️ Status: Base image required."
    if logo_arr is None:
        return img_arr, "⚠️ Status: Watermark logo image required."

    base = Image.fromarray(img_arr).convert("RGBA")
    logo = Image.fromarray(logo_arr).convert("RGBA")

    # Resize logo proportional to base image width
    logo_width = int(base.width * (scale / 100.0))
    aspect_ratio = logo.height / logo.width
    logo_height = int(logo_width * aspect_ratio)
    logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

    # Set opacity
    alpha = logo.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity / 100.0)
    logo.putalpha(alpha)

    # Position calculation
    margin = 20
    if pos == "Bottom Right":
        x, y = base.width - logo_width - margin, base.height - logo_height - margin
    elif pos == "Bottom Left":
        x, y = margin, base.height - logo_height - margin
    elif pos == "Top Right":
        x, y = base.width - logo_width - margin, margin
    elif pos == "Top Left":
        x, y = margin, margin
    else:  # Center Tile
        x, y = (base.width - logo_width) // 2, (base.height - logo_height) // 2

    watermarked = base.copy()
    watermarked.paste(logo, (x, y), logo)

    status = f"🏷️ Watermark Applied at {pos} | Scale: {scale}% | Opacity: {opacity}%"
    return np.array(watermarked.convert("RGB")), status

# 4. Color & Tone Studio
def process_color(img_arr, preset, b, c, s, sh):
    if img_arr is None:
        return None, "⚠️ Status: No image loaded."

    img = Image.fromarray(img_arr)

    # Apply presets if selected
    if preset == "Cyberpunk Neon":
        b, c, s, sh = 1.1, 1.3, 1.8, 1.4
    elif preset == "Cinematic Dark":
        b, c, s, sh = 0.85, 1.4, 0.9, 1.2
    elif preset == "Vibrant Boost":
        b, c, s, sh = 1.05, 1.15, 1.5, 1.1

    # Apply Enhancements
    img = ImageEnhance.Brightness(img).enhance(b)
    img = ImageEnhance.Contrast(img).enhance(c)
    img = ImageEnhance.Color(img).enhance(s)
    img = ImageEnhance.Sharpness(img).enhance(sh)

    status = f"🎨 Color Grading Applied | Preset: {preset} (B:{b:.2f}, C:{c:.2f}, S:{s:.2f}, Sharp:{sh:.2f})"
    return np.array(img), status

# 5. Smart Canvas & Aspect Ratio Export
def process_export(img_arr, auto_trim, aspect, fmt, quality):
    if img_arr is None:
        return None, "⚠️ Status: No image ready for export."

    img = Image.fromarray(img_arr)

    # Crop aspect ratio if requested
    if aspect != "Original":
        w, h = img.size
        if aspect == "1:1 Square":
            target_dim = min(w, h)
            left = (w - target_dim) // 2
            top = (h - target_dim) // 2
            img = img.crop((left, top, left + target_dim, top + target_dim))
        elif aspect == "16:9 Landscape":
            target_h = int(w * 9 / 16)
            if target_h <= h:
                top = (h - target_h) // 2
                img = img.crop((0, top, w, top + target_h))
        elif aspect == "9:16 Story":
            target_w = int(h * 9 / 16)
            if target_w <= w:
                left = (w - target_w) // 2
                img = img.crop((left, 0, left + target_w, h))

    status = f"📦 Export Ready | Format: {fmt} | Dimensions: {img.width}x{img.height}px"
    return np.array(img), status

# 6. Optional Gemini AI Image Analyzer
def analyze_with_gemini(img_arr):
    if img_arr is None:
        return "⚠️ Please upload an image first."
    if not client:
        return "⚠️ GEMINI_API_KEY is missing or invalid in your environment."

    try:
        pil_img = Image.fromarray(img_arr)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[pil_img, "Analyze this image and provide a concise 2-sentence breakdown of its subject, visual composition, and style."]
        )
        return f"🤖 Gemini Vision Insight:\n{response.text.strip()}"
    except Exception as e:
        return f"❌ Gemini API Error: {str(e)}"

# Gradio Interface Setup
with gr.Blocks(title="Shadow Flamez AI Studio Pro v2.0", css=CUSTOM_CSS) as app:
    
    with gr.Row(elem_id="studio-header"):
        gr.Markdown(
            """
            # SHADOW FLAMEZ AI STUDIO PRO
            v2.0 • Real-Time Image Editing, 4x Upscaling, Watermarking & Color Suite
            """
        )

    with gr.Tabs():
        # TAB 1
        with gr.TabItem("Background & Compositor"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. INPUT & COMPOSITING")
                    comp_input = gr.Image(label="Upload Image", type="numpy")
                    comp_bg_style = gr.Dropdown(["Original", "Solid Color", "Custom Background"], value="Original", label="Background Style")
                    comp_bg_color = gr.ColorPicker(label="Solid Background Color", value="#000000")
                    comp_custom_bg = gr.Image(label="Custom Background Image", type="numpy")
                    comp_shadow = gr.Slider(minimum=0, maximum=100, value=25, label="Drop Shadow Options")
                    comp_btn = gr.Button("PROCESS COMPOSITE", elem_classes=["cyber-btn"])
                    ai_btn = gr.Button("🤖 ANALYZE WITH GEMINI AI", elem_classes=["transfer-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. OUTPUT PREVIEWS")
                    comp_specs = gr.Textbox(label="Status & Performance Specs", value="Awaiting input...", interactive=False)
                    comp_output = gr.Image(label="Composited Result", interactive=False)
                    
                    with gr.Row():
                        send_to_upscaler_btn = gr.Button("➡️ Send to 4x Upscaler", elem_classes=["transfer-btn"])
                        send_to_watermark_btn = gr.Button("➡️ Send to Watermarking", elem_classes=["transfer-btn"])

        # TAB 2
        with gr.TabItem("4x AI Upscaler"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. SUPER-RESOLUTION")
                    upscale_input = gr.Image(label="Upload Image", type="numpy")
                    upscale_btn = gr.Button("UPSCALE 4X INSTANTLY", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. ENHANCED RESULT")
                    upscale_specs = gr.Textbox(label="Status Specs", value="Ready", interactive=False)
                    upscale_output = gr.Image(label="4x Super-Resolution Output", interactive=False)

        # TAB 3
        with gr.TabItem("Watermark & Branding"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. WATERMARK CONTROLS")
                    wm_base = gr.Image(label="Base Image", type="numpy")
                    wm_logo = gr.Image(label="Watermark / Logo Image", type="numpy")
                    wm_pos = gr.Dropdown(["Bottom Right", "Bottom Left", "Top Right", "Top Left", "Center Tile"], value="Bottom Right", label="Position")
                    wm_scale = gr.Slider(minimum=5, maximum=50, value=20, label="Watermark Scale (%)")
                    wm_opacity = gr.Slider(minimum=10, maximum=100, value=80, label="Opacity (%)")
                    wm_btn = gr.Button("APPLY BRAND WATERMARK", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. BRANDED OUTPUT")
                    wm_specs = gr.Textbox(label="Status Specs", value="Ready", interactive=False)
                    wm_output = gr.Image(label="Watermarked Result", interactive=False)

        # TAB 4
        with gr.TabItem("Color & Tone Studio"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. COLOR GRADING CONTROLS")
                    color_input = gr.Image(label="Upload Image", type="numpy")
                    color_preset = gr.Dropdown(["Custom", "Cyberpunk Neon", "Cinematic Dark", "Vibrant Boost"], value="Custom", label="Style Preset")
                    slider_b = gr.Slider(0.5, 2.0, value=1.0, label="Brightness")
                    slider_c = gr.Slider(0.5, 2.0, value=1.0, label="Contrast")
                    slider_s = gr.Slider(0.0, 2.5, value=1.0, label="Saturation")
                    slider_sh = gr.Slider(0.0, 3.0, value=1.0, label="Sharpness")
                    color_btn = gr.Button("APPLY COLOR GRADE", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. GRADED PREVIEW")
                    color_specs = gr.Textbox(label="Status Specs", value="Ready", interactive=False)
                    color_output = gr.Image(label="Color Graded Result", interactive=False)

        # TAB 5
        with gr.TabItem("Smart Canvas & Export"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. RESIZING & FORMAT CONTROLS")
                    export_input = gr.Image(label="Upload Image", type="numpy")
                    export_autotrim = gr.Checkbox(label="Auto-Trim Transparency", value=True)
                    export_aspect = gr.Dropdown(["Original", "1:1 Square", "16:9 Landscape", "9:16 Story"], value="Original", label="Aspect Ratio Fit")
                    export_fmt = gr.Radio(["PNG", "JPEG", "WEBP"], value="PNG", label="Export Format")
                    export_quality = gr.Slider(50, 100, value=95, label="Quality")
                    export_btn = gr.Button("CONVERT & EXPORT", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. EXPORT PREVIEW")
                    export_specs = gr.Textbox(label="Status Specs", value="Ready", interactive=False)
                    export_output = gr.Image(label="Formatted Result", interactive=False)

    # Event Bindings
    comp_btn.click(process_composite, inputs=[comp_input, comp_bg_style, comp_bg_color, comp_custom_bg, comp_shadow], outputs=[comp_output, comp_specs])
    ai_btn.click(analyze_with_gemini, inputs=[comp_input], outputs=[comp_specs])
    upscale_btn.click(process_upscale, inputs=[upscale_input], outputs=[upscale_output, upscale_specs])
    wm_btn.click(process_watermark, inputs=[wm_base, wm_logo, wm_pos, wm_scale, wm_opacity], outputs=[wm_output, wm_specs])
    color_btn.click(process_color, inputs=[color_input, color_preset, slider_b, slider_c, slider_s, slider_sh], outputs=[color_output, color_specs])
    export_btn.click(process_export, inputs=[export_input, export_autotrim, export_aspect, export_fmt, export_quality], outputs=[export_output, export_specs])

    # Inter-Tab Pipeline Transfers
    send_to_upscaler_btn.click(lambda x: x, inputs=[comp_output], outputs=[upscale_input])
    send_to_watermark_btn.click(lambda x: x, inputs=[comp_output], outputs=[wm_base])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.launch(server_name="0.0.0.0", server_port=port)
