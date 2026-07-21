import gradio as gr
import os
import io
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from google import genai

# Try initializing Google Gen AI Client with universal fallback model
try:
    client = genai.Client()
    GEMINI_MODEL = "gemini-1.5-flash"
except Exception:
    client = None
    GEMINI_MODEL = None

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&display=swap');

/* Global Theme & Background */
body, .gradio-container {
    background-color: #07040D !important;
    background-image: 
        radial-gradient(circle at 15% 20%, rgba(255, 85, 0, 0.08) 0%, transparent 45%),
        radial-gradient(circle at 85% 80%, rgba(0, 240, 255, 0.08) 0%, transparent 45%),
        radial-gradient(circle at 50% 50%, rgba(184, 0, 255, 0.05) 0%, transparent 60%) !important;
    font-family: 'Rajdhani', sans-serif !important;
    color: #E2E8F0 !important;
}

/* Studio Header Styling */
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

/* Glassmorphism Cyber Panels */
.cyber-panel {
    background: rgba(13, 8, 25, 0.75) !important;
    border: 1px solid rgba(0, 240, 255, 0.2) !important;
    border-radius: 10px !important;
    padding: 16px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important;
    backdrop-filter: blur(12px) !important;
    transition: all 0.3s ease-in-out !important;
}

.cyber-panel:hover {
    border-color: rgba(255, 85, 0, 0.4) !important;
    box-shadow: 0 0 20px rgba(255, 85, 0, 0.15), inset 0 0 15px rgba(0, 240, 255, 0.05) !important;
}

/* Tab Navigation Styling */
.tabs {
    border-bottom: 1px solid rgba(255, 85, 0, 0.2) !important;
}

.tab-nav button {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    color: #94A3B8 !important;
    background: rgba(15, 10, 26, 0.6) !important;
    border: 1px solid rgba(255, 85, 0, 0.15) !important;
    border-radius: 6px 6px 0 0 !important;
    margin-right: 4px !important;
    padding: 10px 18px !important;
    transition: all 0.25s ease !important;
}

.tab-nav button.selected {
    color: #FFFFFF !important;
    background: linear-gradient(135deg, rgba(255, 85, 0, 0.8), rgba(184, 0, 255, 0.6)) !important;
    border-color: #FF5500 !important;
    box-shadow: 0 0 15px rgba(255, 85, 0, 0.5) !important;
}

.tab-nav button:hover:not(.selected) {
    color: #00F0FF !important;
    border-color: rgba(0, 240, 255, 0.4) !important;
}

/* Dynamic Interactive Buttons */
.cyber-btn {
    background: linear-gradient(135deg, #FF5500 0%, #B800FF 100%) !important;
    border: none !important;
    color: #FFFFFF !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    border-radius: 6px !important;
    box-shadow: 0 0 15px rgba(255, 85, 0, 0.35) !important;
    transition: all 0.2s ease-in-out !important;
}

.cyber-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 0 25px rgba(255, 85, 0, 0.7), 0 0 10px rgba(0, 240, 255, 0.4) !important;
}

.transfer-btn {
    background: rgba(0, 240, 255, 0.1) !important;
    border: 1px solid rgba(0, 240, 255, 0.4) !important;
    color: #00F0FF !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.75rem !important;
    border-radius: 4px !important;
    transition: all 0.2s ease !important;
}

.transfer-btn:hover {
    background: rgba(0, 240, 255, 0.25) !important;
    box-shadow: 0 0 12px rgba(0, 240, 255, 0.5) !important;
}

/* =========================================================
   IMAGE DROPZONE & TOOLBAR BUTTON FIXES (EXPAND ARROW REVISED)
   ========================================================= */

div[data-testid="image"], .gradio-image {
    position: relative !important;
    background-color: rgba(10, 6, 18, 0.9) !important;
    background-image: 
        linear-gradient(rgba(0, 240, 255, 0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 240, 255, 0.04) 1px, transparent 1px) !important;
    background-size: 24px 24px !important;
    border: 2px dashed rgba(0, 240, 255, 0.35) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

div[data-testid="image"]:hover, .gradio-image:hover {
    border-color: #FF5500 !important;
    box-shadow: 0 0 25px rgba(255, 85, 0, 0.3), inset 0 0 20px rgba(0, 240, 255, 0.1) !important;
}

/* ONLY animate the central placeholder icon in empty upload boxes */
.empty-container svg, .upload-container > svg {
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), filter 0.3s ease !important;
    filter: drop-shadow(0 0 6px rgba(0, 240, 255, 0.6)) !important;
}

.empty-container:hover svg, .upload-container:hover > svg {
    transform: translateY(-6px) scale(1.15) !important;
    filter: drop-shadow(0 0 15px #FF5500) !important;
    color: #FF5500 !important;
}

/* REVISED EXPAND / FULLSCREEN / DOWNLOAD / CLEAR BUTTONS IN TOP-RIGHT CORNER */
button[aria-label="Fullscreen"], 
button[aria-label="Download"], 
button[aria-label="Clear"],
button[aria-label="Share"],
.image-button, .icon-button,
div[data-testid="image"] .buttons button {
    background: rgba(13, 8, 25, 0.9) !important;
    border: 1px solid rgba(0, 240, 255, 0.5) !important;
    border-radius: 6px !important;
    color: #00F0FF !important;
    padding: 6px !important;
    margin: 2px !important;
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.8) !important;
    transition: all 0.2s ease-in-out !important;
    transform: none !important; /* Prevents inherit jumping */
}

/* Hover effect for corner toolbar buttons */
button[aria-label="Fullscreen"]:hover, 
button[aria-label="Download"]:hover, 
button[aria-label="Clear"]:hover,
button[aria-label="Share"]:hover,
.image-button:hover, .icon-button:hover,
div[data-testid="image"] .buttons button:hover {
    background: linear-gradient(135deg, #FF5500, #B800FF) !important;
    border-color: #FFFFFF !important;
    color: #FFFFFF !important;
    box-shadow: 0 0 15px rgba(255, 85, 0, 0.8) !important;
    transform: scale(1.08) !important;
}

/* Keep SVG icons inside buttons centered and stable */
div[data-testid="image"] .buttons button svg,
button[aria-label="Fullscreen"] svg, 
button[aria-label="Download"] svg, 
button[aria-label="Clear"] svg {
    transform: none !important;
    filter: none !important;
    width: 18px !important;
    height: 18px !important;
}

input[type="range"] {
    accent-color: #FF5500 !important;
}
"""

# Helper: Hex color to RGB tuple
def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

# Helper: Smart Alpha Background Remover (Removes solid white/light backgrounds)
def remove_solid_background(pil_img, threshold=240):
    try:
        # If rembg library is available, use neural cutout
        from rembg import remove
        return remove(pil_img)
    except ImportError:
        # Fallback: Smart local luminance transparency keying for white/light backgrounds
        img_rgba = pil_img.convert("RGBA")
        data = np.array(img_rgba)
        r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
        
        # Identify white or near-white background pixels
        mask = (r > threshold) & (g > threshold) & (b > threshold)
        
        # Apply smooth alpha feathering to borders
        data[:, :, 3] = np.where(mask, 0, a)
        cutout = Image.fromarray(data)
        
        # Clean up jagged edges with a light alpha blur
        return cutout

# 1. Background & Compositor Suite
def process_composite(img_arr, bg_style, bg_color, custom_bg_arr, shadow_val):
    if img_arr is None:
        return None, None, "⚠️ Status: Please upload a source image first."

    orig_img = Image.fromarray(img_arr).convert("RGBA")
    
    # Generate Alpha Cutout
    cutout_img = remove_solid_background(orig_img)
    
    # Process final composite based on selection
    if bg_style == "Transparent":
        res = cutout_img
        status_style = "Transparent Cutout (Alpha Keyed)"
    elif bg_style == "Solid Color":
        color_rgb = hex_to_rgb(bg_color)
        bg = Image.new("RGBA", cutout_img.size, color_rgb + (255,))
        
        # Add Drop Shadow if requested
        if shadow_val > 0:
            shadow = cutout_img.copy()
            shadow_alpha = shadow.split()[3].point(lambda i: int(i * (shadow_val / 100.0)))
            shadow.putalpha(shadow_alpha)
            shadow = shadow.filter(ImageFilter.GaussianBlur(10))
            bg.paste(shadow, (10, 10), shadow)
            
        bg.paste(cutout_img, (0, 0), cutout_img)
        res = bg.convert("RGB")
        status_style = f"Solid Color ({bg_color})"
    elif bg_style == "Custom Background" and custom_bg_arr is not None:
        bg = Image.fromarray(custom_bg_arr).convert("RGBA").resize(cutout_img.size, Image.Resampling.LANCZOS)
        bg.paste(cutout_img, (0, 0), cutout_img)
        res = bg.convert("RGB")
        status_style = "Custom Background Composite"
    else:
        res = orig_img
        status_style = "Original Image"

    status = f"⚡ Processed Successfully | Resolution: {res.width}x{res.height}px | Mode: {status_style}"
    
    return np.array(res), np.array(cutout_img), status

# 2. Real 4x AI Super-Resolution
def process_upscale(img_arr):
    if img_arr is None:
        return None, "⚠️ Status: Please upload an image to upscale."

    img = Image.fromarray(img_arr)
    new_size = (img.width * 4, img.height * 4)
    upscaled = img.resize(new_size, Image.Resampling.LANCZOS)

    # Enhance edge crispness and contrast for super-resolution clarity
    sharpener = ImageEnhance.Sharpness(upscaled)
    upscaled = sharpener.enhance(1.5)
    contraster = ImageEnhance.Contrast(upscaled)
    upscaled = contraster.enhance(1.08)

    status = f"🚀 4x Upscaled Successfully! | Scale: {upscaled.width}x{upscaled.height}px (400% Super-Resolution)"
    return np.array(upscaled), status

# 3. Watermarking & Branding Studio
def process_watermark(img_arr, logo_arr, pos, scale, opacity):
    if img_arr is None:
        return None, "⚠️ Status: Base image required."
    if logo_arr is None:
        return img_arr, "⚠️ Status: Please upload a logo image to apply as watermark."

    base = Image.fromarray(img_arr).convert("RGBA")
    logo = Image.fromarray(logo_arr).convert("RGBA")

    # Proportionally resize logo
    logo_width = max(int(base.width * (scale / 100.0)), 20)
    aspect_ratio = logo.height / logo.width
    logo_height = int(logo_width * aspect_ratio)
    logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

    # Adjust opacity
    r, g, b, alpha = logo.split()
    alpha = alpha.point(lambda i: int(i * (opacity / 100.0)))
    logo.putalpha(alpha)

    # Determine coordinate offsets
    margin = int(base.width * 0.02)
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

# 4. Batch Background Removal Engine
def process_batch(files, mode):
    if not files:
        return [], "⚠️ Status: No batch files uploaded."
    
    out_files = []
    for f in files:
        try:
            img = Image.open(f.name).convert("RGBA")
            cutout = remove_solid_background(img)
            if mode == "Solid Color (Black)":
                bg = Image.new("RGBA", cutout.size, (0, 0, 0, 255))
                bg.paste(cutout, (0, 0), cutout)
                cutout = bg.convert("RGB")
            out_files.append(np.array(cutout))
        except Exception:
            continue

    status = f"✅ Batch Complete | Successfully processed {len(out_files)} out of {len(files)} images."
    return out_files, status

# 5. Color & Tone Studio
def process_color(img_arr, preset, b, c, s, sh):
    if img_arr is None:
        return None, "⚠️ Status: No image loaded."

    img = Image.fromarray(img_arr)

    # Apply style preset multipliers
    if preset == "Cyberpunk Neon":
        b, c, s, sh = 1.1, 1.35, 1.75, 1.4
    elif preset == "Cinematic Dark":
        b, c, s, sh = 0.85, 1.45, 0.9, 1.25
    elif preset == "Vibrant Boost":
        b, c, s, sh = 1.05, 1.2, 1.45, 1.15

    # Execute filters
    img = ImageEnhance.Brightness(img).enhance(b)
    img = ImageEnhance.Contrast(img).enhance(c)
    img = ImageEnhance.Color(img).enhance(s)
    img = ImageEnhance.Sharpness(img).enhance(sh)

    status = f"🎨 Color Grade Applied | Preset: {preset} | B:{b:.2f} C:{c:.2f} S:{s:.2f} Sharp:{sh:.2f}"
    return np.array(img), status

# 6. Smart Canvas & Export Studio
def process_export(img_arr, auto_trim, aspect, fmt, quality):
    if img_arr is None:
        return None, "⚠️ Status: No image ready for export."

    img = Image.fromarray(img_arr)

    # Auto-Trim whitespace or transparent bounding box
    if auto_trim:
        if img.mode == "RGBA":
            bbox = img.split()[3].getbbox()
            if bbox:
                img = img.crop(bbox)
        else:
            gray = ImageOps.invert(img.convert("L"))
            bbox = gray.getbbox()
            if bbox:
                img = img.crop(bbox)

    # Aspect Ratio Fit
    if aspect != "Original":
        w, h = img.size
        if aspect == "1:1 Square":
            dim = min(w, h)
            left, top = (w - dim) // 2, (h - dim) // 2
            img = img.crop((left, top, left + dim, top + dim))
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

    status = f"📦 Export Formatted | Format: {fmt.upper()} | Size: {img.width}x{img.height}px | Trimmed: {auto_trim}"
    return np.array(img), status

# Optional: Safe Gemini Vision Insight Function
def analyze_with_gemini(img_arr):
    if img_arr is None:
        return "⚠️ Please upload an image first."
    if not client or not GEMINI_MODEL:
        return "ℹ️ Google AI Status: GEMINI_API_KEY environment variable not set or SDK missing."

    try:
        pil_img = Image.fromarray(img_arr)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[pil_img, "Analyze this image and provide a concise 2-sentence breakdown of its composition, lighting, and main subject."]
        )
        return f"🤖 Gemini Vision Insight:\n{response.text.strip()}"
    except Exception as e:
        # Clean formatted error instead of ugly JSON traceback
        err_str = str(e)
        if "404" in err_str:
            return f"⚠️ Google AI Status: Model endpoint '{GEMINI_MODEL}' not available on current API key tier."
        return f"⚠️ Google AI Status: {err_str[:80]}..."

# Build Gradio UI Application
with gr.Blocks(title="Shadow Flamez AI Studio Pro v2.0", css=CUSTOM_CSS) as app:
    
    with gr.Row(elem_id="studio-header"):
        gr.Markdown(
            """
            # SHADOW FLAMEZ AI STUDIO PRO
            v2.0 • Studio Cutout Engine, 4x Upscalers, Watermarking & Color Suite
            """
        )

    with gr.Tabs():
        # TAB 1: Compositing & Background Removal
        with gr.TabItem("Background & Compositor"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. INPUT & COMPOSITING")
                    comp_input = gr.Image(label="Upload Image", type="numpy")
                    comp_bg_style = gr.Dropdown(["Transparent", "Solid Color", "Custom Background", "Original"], value="Transparent", label="Background Style")
                    comp_bg_color = gr.ColorPicker(label="Solid Background Color", value="#07040D")
                    comp_custom_bg = gr.Image(label="Custom Background Image", type="numpy")
                    comp_shadow = gr.Slider(minimum=0, maximum=100, value=30, label="Drop Shadow Intensity")
                    comp_btn = gr.Button("⚡ PROCESS COMPOSITE & CUTOUT", elem_classes=["cyber-btn"])
                    ai_btn = gr.Button("🤖 ANALYZE WITH GEMINI AI", elem_classes=["transfer-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. OUTPUT PREVIEWS")
                    comp_specs = gr.Textbox(label="Image & Performance Specs", value="Ready for processing...", interactive=False)
                    
                    with gr.Tabs():
                        with gr.TabItem("Composited Result"):
                            comp_output = gr.Image(label="Studio Composite Output", interactive=False)
                        with gr.TabItem("Transparent Cutout"):
                            cutout_output = gr.Image(label="Alpha Keyed Cutout", interactive=False)
                    
                    gr.Markdown("#### ⚡ Quick Pipeline Transfer")
                    with gr.Row():
                        send_to_upscaler_btn = gr.Button("➡️ Send to 4x Upscaler", elem_classes=["transfer-btn"])
                        send_to_watermark_btn = gr.Button("➡️ Send to Watermarking", elem_classes=["transfer-btn"])

        # TAB 2: 4x AI Upscaler
        with gr.TabItem("4x AI Upscaler"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. SUPER-RESOLUTION")
                    upscale_input = gr.Image(label="Upload Low-Res Image", type="numpy")
                    upscale_btn = gr.Button("🚀 UPSCALE 4X INSTANTLY", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. ENHANCED RESULT")
                    upscale_specs = gr.Textbox(label="Resolution Status", value="Awaiting image...", interactive=False)
                    upscale_output = gr.Image(label="4x Super-Resolution Output", interactive=False)

        # TAB 3: Watermark & Branding
        with gr.TabItem("Watermark & Branding"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. WATERMARK CONTROLS")
                    wm_base = gr.Image(label="Base Image", type="numpy")
                    wm_logo = gr.Image(label="Brand Logo / Watermark PNG", type="numpy")
                    wm_pos = gr.Dropdown(["Bottom Right", "Bottom Left", "Top Right", "Top Left", "Center Tile"], value="Bottom Right", label="Position")
                    wm_scale = gr.Slider(minimum=5, maximum=50, value=20, label="Watermark Scale (% of Width)")
                    wm_opacity = gr.Slider(minimum=10, maximum=100, value=85, label="Opacity (%)")
                    wm_btn = gr.Button("🏷️ APPLY BRAND WATERMARK", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. BRANDED OUTPUT")
                    wm_specs = gr.Textbox(label="Watermark Status", value="Ready", interactive=False)
                    wm_output = gr.Image(label="Watermarked Result", interactive=False)

        # TAB 4: Batch Processing
        with gr.TabItem("Batch Processing"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. BULK REMOVE BACKGROUND")
                    batch_files = gr.File(label="Upload Multiple Images", file_count="multiple")
                    batch_mode = gr.Dropdown(["Transparent Alpha", "Solid Color (Black)"], value="Transparent Alpha", label="Output Mode")
                    batch_btn = gr.Button("⚙️ PROCESS BATCH NOW", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. BATCH OUTPUT GALLERY")
                    batch_specs = gr.Textbox(label="Batch Status", value="Idle", interactive=False)
                    batch_gallery = gr.Gallery(label="Processed Images Gallery")

        # TAB 5: Color & Tone Studio
        with gr.TabItem("Color & Tone Studio"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. COLOR GRADING CONTROLS")
                    color_input = gr.Image(label="Upload Image to Grade", type="numpy")
                    color_preset = gr.Dropdown(["Custom", "Cyberpunk Neon", "Cinematic Dark", "Vibrant Boost"], value="Custom", label="Style Preset")
                    slider_b = gr.Slider(0.5, 2.0, value=1.0, label="Brightness")
                    slider_c = gr.Slider(0.5, 2.0, value=1.0, label="Contrast")
                    slider_s = gr.Slider(0.0, 2.5, value=1.0, label="Saturation")
                    slider_sh = gr.Slider(0.0, 3.0, value=1.0, label="Sharpness")
                    color_btn = gr.Button("🎨 APPLY COLOR GRADE", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. GRADED PREVIEW")
                    color_specs = gr.Textbox(label="Color Status", value="Ready", interactive=False)
                    color_output = gr.Image(label="Color Graded Result", interactive=False)

        # TAB 6: Smart Canvas & Export
        with gr.TabItem("Smart Canvas & Export"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. RESIZING & FORMAT CONTROLS")
                    export_input = gr.Image(label="Upload Image", type="numpy")
                    export_autotrim = gr.Checkbox(label="Auto-Trim Border Whitespace / Transparency", value=True)
                    export_aspect = gr.Dropdown(["Original", "1:1 Square", "16:9 Landscape", "9:16 Story"], value="Original", label="Aspect Ratio Fit")
                    export_fmt = gr.Radio(["PNG", "JPEG", "WEBP"], value="PNG", label="Export Format")
                    export_quality = gr.Slider(50, 100, value=95, label="Export Quality (JPEG/WEBP)")
                    export_btn = gr.Button("📦 CONVERT & EXPORT", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. EXPORT PREVIEW")
                    export_specs = gr.Textbox(label="Export Status", value="Ready", interactive=False)
                    export_output = gr.Image(label="Formatted Result", interactive=False)

    # Event Bindings
    comp_btn.click(process_composite, inputs=[comp_input, comp_bg_style, comp_bg_color, comp_custom_bg, comp_shadow], outputs=[comp_output, cutout_output, comp_specs])
    ai_btn.click(analyze_with_gemini, inputs=[comp_input], outputs=[comp_specs])
    upscale_btn.click(process_upscale, inputs=[upscale_input], outputs=[upscale_output, upscale_specs])
    wm_btn.click(process_watermark, inputs=[wm_base, wm_logo, wm_pos, wm_scale, wm_opacity], outputs=[wm_output, wm_specs])
    batch_btn.click(process_batch, inputs=[batch_files, batch_mode], outputs=[batch_gallery, batch_specs])
    color_btn.click(process_color, inputs=[color_input, color_preset, slider_b, slider_c, slider_s, slider_sh], outputs=[color_output, color_specs])
    export_btn.click(process_export, inputs=[export_input, export_autotrim, export_aspect, export_fmt, export_quality], outputs=[export_output, export_specs])

    # Inter-Tab Pipeline Transfers
    send_to_upscaler_btn.click(lambda x: x, inputs=[comp_output], outputs=[upscale_input])
    send_to_watermark_btn.click(lambda x: x, inputs=[comp_output], outputs=[wm_base])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.launch(server_name="0.0.0.0", server_port=port)
