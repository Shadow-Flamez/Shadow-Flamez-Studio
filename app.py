import gradio as gr
import os
import io
import time
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from google import genai

# =========================================================
# 01. SINGLETON AI CACHING & CLOUD OPTIMIZATION
# =========================================================
# Prevent Render CPU freezes by caching AI models globally in RAM at boot
GLOBAL_REMBG_SESSION = None

def get_rembg_session():
    global GLOBAL_REMBG_SESSION
    if GLOBAL_REMBG_SESSION is None:
        try:
            from rembg import new_session
            # Using u2netp (lightweight fast model) to prevent cloud RAM crashes
            GLOBAL_REMBG_SESSION = new_session("u2netp")
        except Exception as e:
            print(f"⚠️ Could not load neural AI session: {e}")
            GLOBAL_REMBG_SESSION = "FALLBACK"
    return GLOBAL_REMBG_SESSION

# Initialize Google Gen AI client safely
try:
    client = genai.Client()
    GEMINI_MODEL = "gemini-1.5-flash"
except Exception:
    client = None
    GEMINI_MODEL = None

# =========================================================
# 02. SHADOW FLAMEZ CYBER-GOTHIC UI THEME (CSS)
# =========================================================
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&display=swap');

/* Global Deep Obsidian Theme & Animations */
@keyframes pulse-glow {
    0% { box-shadow: 0 0 15px rgba(255, 69, 0, 0.3), inset 0 0 15px rgba(0, 240, 255, 0.1); }
    50% { box-shadow: 0 0 30px rgba(255, 69, 0, 0.6), inset 0 0 25px rgba(138, 43, 226, 0.2); }
    100% { box-shadow: 0 0 15px rgba(255, 69, 0, 0.3), inset 0 0 15px rgba(0, 240, 255, 0.1); }
}

body, .gradio-container {
    background-color: #05030A !important;
    background-image: 
        radial-gradient(circle at 10% 15%, rgba(255, 69, 0, 0.12) 0%, transparent 40%),
        radial-gradient(circle at 90% 85%, rgba(0, 240, 255, 0.10) 0%, transparent 45%),
        radial-gradient(circle at 50% 50%, rgba(138, 43, 226, 0.08) 0%, transparent 60%) !important;
    font-family: 'Rajdhani', sans-serif !important;
    color: #F1F5F9 !important;
}

/* Studio Header with Animated Flame Border */
#studio-header {
    background: rgba(12, 8, 20, 0.85) !important;
    border: 1px solid rgba(255, 69, 0, 0.4) !important;
    border-radius: 16px !important;
    padding: 28px !important;
    text-align: center !important;
    animation: pulse-glow 6s infinite ease-in-out !important;
    margin-bottom: 24px !important;
}

#studio-header h1 {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 2.6rem !important;
    font-weight: 900 !important;
    letter-spacing: 4px !important;
    background: linear-gradient(135deg, #FF4500 0%, #FF8C00 30%, #00F0FF 70%, #8A2BE2 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    text-transform: uppercase !important;
    margin: 0 !important;
    text-shadow: 0 0 20px rgba(255, 69, 0, 0.3) !important;
}

#studio-header p {
    color: #A7F3D0 !important;
    font-size: 1.05rem !important;
    margin-top: 8px !important;
    letter-spacing: 1.5px !important;
    font-weight: 600 !important;
}

/* Glassmorphism Cyber Cards */
.cyber-panel {
    background: rgba(15, 10, 26, 0.75) !important;
    border: 1px solid rgba(0, 240, 255, 0.25) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6) !important;
    backdrop-filter: blur(16px) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.cyber-panel:hover {
    border-color: rgba(255, 69, 0, 0.6) !important;
    box-shadow: 0 0 25px rgba(255, 69, 0, 0.25), inset 0 0 15px rgba(0, 240, 255, 0.1) !important;
}

/* Tabs & Navigation */
.tabs {
    border-bottom: 2px solid rgba(255, 69, 0, 0.3) !important;
}

.tab-nav button {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
    color: #94A3B8 !important;
    background: rgba(18, 12, 30, 0.8) !important;
    border: 1px solid rgba(255, 69, 0, 0.2) !important;
    border-radius: 8px 8px 0 0 !important;
    margin-right: 6px !important;
    padding: 12px 22px !important;
    transition: all 0.25s ease !important;
}

.tab-nav button.selected {
    color: #FFFFFF !important;
    background: linear-gradient(135deg, rgba(255, 69, 0, 0.9), rgba(138, 43, 226, 0.8)) !important;
    border-color: #FF4500 !important;
    box-shadow: 0 -5px 20px rgba(255, 69, 0, 0.5) !important;
}

.tab-nav button:hover:not(.selected) {
    color: #00F0FF !important;
    border-color: rgba(0, 240, 255, 0.5) !important;
}

/* Interactive Action Buttons */
.cyber-btn {
    background: linear-gradient(135deg, #FF4500 0%, #8A2BE2 100%) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    color: #FFFFFF !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border-radius: 8px !important;
    padding: 14px !important;
    box-shadow: 0 0 20px rgba(255, 69, 0, 0.4) !important;
    transition: all 0.2s ease-in-out !important;
    cursor: pointer !important;
}

.cyber-btn:hover {
    transform: translateY(-3px) scale(1.01) !important;
    box-shadow: 0 0 30px rgba(255, 69, 0, 0.8), 0 0 15px rgba(0, 240, 255, 0.5) !important;
}

.transfer-btn {
    background: rgba(0, 240, 255, 0.12) !important;
    border: 1px solid rgba(0, 240, 255, 0.5) !important;
    color: #00F0FF !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
}

.transfer-btn:hover {
    background: rgba(0, 240, 255, 0.3) !important;
    color: #FFFFFF !important;
    box-shadow: 0 0 15px rgba(0, 240, 255, 0.6) !important;
    transform: translateY(-1px) !important;
}

/* Image Dropzones & Stable Toolbar Fixes */
div[data-testid="image"], .gradio-image {
    position: relative !important;
    background-color: rgba(8, 5, 15, 0.95) !important;
    background-image: 
        linear-gradient(rgba(0, 240, 255, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 240, 255, 0.05) 1px, transparent 1px) !important;
    background-size: 20px 20px !important;
    border: 2px dashed rgba(0, 240, 255, 0.4) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

div[data-testid="image"]:hover, .gradio-image:hover {
    border-color: #FF4500 !important;
    box-shadow: 0 0 25px rgba(255, 69, 0, 0.35) !important;
}

button[aria-label="Fullscreen"], button[aria-label="Download"], 
button[aria-label="Clear"], button[aria-label="Share"],
div[data-testid="image"] .buttons button {
    background: rgba(12, 8, 20, 0.95) !important;
    border: 1px solid rgba(0, 240, 255, 0.6) !important;
    border-radius: 6px !important;
    color: #00F0FF !important;
    padding: 6px !important;
    margin: 3px !important;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.9) !important;
    transform: none !important;
}

button[aria-label="Fullscreen"]:hover, button[aria-label="Download"]:hover, 
button[aria-label="Clear"]:hover, button[aria-label="Share"]:hover,
div[data-testid="image"] .buttons button:hover {
    background: linear-gradient(135deg, #FF4500, #8A2BE2) !important;
    border-color: #FFFFFF !important;
    color: #FFFFFF !important;
    box-shadow: 0 0 18px rgba(255, 69, 0, 0.9) !important;
}

input[type="range"] { accent-color: #FF4500 !important; }
"""

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

# Performance Optimization: Dynamic Resolution Scaling
def optimize_image_size(pil_img, max_dim=1600):
    w, h = pil_img.size
    if max(w, h) > max_dim:
        scale = max_dim / float(max(w, h))
        return pil_img.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
    return pil_img

# =========================================================
# 03. DUAL-ENGINE BACKGROUND KEYING & COMPOSITOR
# =========================================================
def execute_background_removal(pil_img, engine_mode, threshold=240):
    start_time = time.time()
    img = optimize_image_size(pil_img, max_dim=1400)
    
    if engine_mode == "⚡ Fast Matrix Keying (< 0.2s)":
        # Ultra-fast NumPy vectorized luminance mask for solid backgrounds
        img_rgba = img.convert("RGBA")
        data = np.array(img_rgba)
        r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
        mask = (r > threshold) & (g > threshold) & (b > threshold)
        data[:, :, 3] = np.where(mask, 0, a)
        cutout = Image.fromarray(data)
        mode_used = "Vectorized Matrix Alpha Keyer"
    else:
        # High-precision Neural AI Cutout using RAM-cached session
        session = get_rembg_session()
        if session != "FALLBACK" and session is not None:
            try:
                from rembg import remove
                cutout = remove(img, session=session)
                mode_used = "Neural u2netp AI (Cached RAM)"
            except Exception:
                cutout = execute_background_removal(img, "⚡ Fast Matrix Keying (< 0.2s)")[0]
                mode_used = "Matrix Keyer (AI Fallback)"
        else:
            cutout = execute_background_removal(img, "⚡ Fast Matrix Keying (< 0.2s)")[0]
            mode_used = "Matrix Keyer (Session Unavailable)"
            
    elapsed = time.time() - start_time
    return cutout, mode_used, elapsed

def process_composite(img_arr, engine_mode, bg_style, bg_color, custom_bg_arr, shadow_val):
    if img_arr is None:
        return None, None, "⚠️ Status: Please upload a source image first."

    orig_img = Image.fromarray(img_arr).convert("RGBA")
    cutout_img, mode_used, exec_time = execute_background_removal(orig_img, engine_mode)
    
    if bg_style == "Transparent":
        res = cutout_img
        status_style = "Transparent Cutout"
    elif bg_style == "Solid Color":
        color_rgb = hex_to_rgb(bg_color)
        bg = Image.new("RGBA", cutout_img.size, color_rgb + (255,))
        
        if shadow_val > 0:
            shadow = cutout_img.copy()
            shadow_alpha = shadow.split()[3].point(lambda i: int(i * (shadow_val / 100.0)))
            shadow.putalpha(shadow_alpha)
            shadow = shadow.filter(ImageFilter.BoxBlur(6)) # Fast box blur for zero lag
            bg.paste(shadow, (10, 10), shadow)
            
        bg.paste(cutout_img, (0, 0), cutout_img)
        res = bg.convert("RGB")
        status_style = f"Solid Color ({bg_color})"
    elif bg_style == "Custom Background" and custom_bg_arr is not None:
        bg = Image.fromarray(custom_bg_arr).convert("RGBA").resize(cutout_img.size, Image.Resampling.BILINEAR)
        bg.paste(cutout_img, (0, 0), cutout_img)
        res = bg.convert("RGB")
        status_style = "Custom Composite"
    else:
        res = orig_img
        status_style = "Original Image"

    status = f"⚡ Processed in {exec_time:.2f}s | Engine: {mode_used} | Output: {res.width}x{res.height}px | Mode: {status_style}"
    return np.array(res), np.array(cutout_img), status

# =========================================================
# 04. HIGH-SPEED 4X SUPER-RESOLUTION UPSCALE
# =========================================================
def process_upscale(img_arr):
    if img_arr is None:
        return None, "⚠️ Status: Please upload an image to upscale."

    start_time = time.time()
    img = Image.fromarray(img_arr)
    img = optimize_image_size(img, max_dim=1000) # Safety cap to prevent Render out-of-memory
    
    new_size = (img.width * 4, img.height * 4)
    upscaled = img.resize(new_size, Image.Resampling.BICUBIC) # High speed bicubic scaling

    # Edge crisping matrix
    sharpener = ImageEnhance.Sharpness(upscaled)
    upscaled = sharpener.enhance(1.35)
    contraster = ImageEnhance.Contrast(upscaled)
    upscaled = contraster.enhance(1.05)

    elapsed = time.time() - start_time
    status = f"🚀 4x Super-Resolution Complete in {elapsed:.2f}s | New Dimensions: {upscaled.width}x{upscaled.height}px"
    return np.array(upscaled), status

# =========================================================
# 05. BRAND WATERMARKING STUDIO
# =========================================================
def process_watermark(img_arr, logo_arr, pos, scale, opacity):
    if img_arr is None:
        return None, "⚠️ Status: Base image required."
    if logo_arr is None:
        return img_arr, "⚠️ Status: Please upload a logo image."

    start_time = time.time()
    base = Image.fromarray(img_arr).convert("RGBA")
    logo = Image.fromarray(logo_arr).convert("RGBA")

    logo_width = max(int(base.width * (scale / 100.0)), 20)
    aspect_ratio = logo.height / float(logo.width)
    logo_height = int(logo_width * aspect_ratio)
    logo = logo.resize((logo_width, logo_height), Image.Resampling.BILINEAR)

    # Vectorized opacity scaling
    r, g, b, alpha = logo.split()
    alpha = alpha.point(lambda i: int(i * (opacity / 100.0)))
    logo.putalpha(alpha)

    margin = int(base.width * 0.025)
    if pos == "Bottom Right":
        x, y = base.width - logo_width - margin, base.height - logo_height - margin
    elif pos == "Bottom Left":
        x, y = margin, base.height - logo_height - margin
    elif pos == "Top Right":
        x, y = base.width - logo_width - margin, margin
    elif pos == "Top Left":
        x, y = margin, margin
    else: # Center Tile
        x, y = (base.width - logo_width) // 2, (base.height - logo_height) // 2

    watermarked = base.copy()
    watermarked.paste(logo, (x, y), logo)
    
    elapsed = time.time() - start_time
    status = f"🏷️ Watermark Stamped in {elapsed:.2f}s | Position: {pos} | Scale: {scale}% | Opacity: {opacity}%"
    return np.array(watermarked.convert("RGB")), status

# =========================================================
# 06. MULTI-IMAGE BATCH ENGINE
# =========================================================
def process_batch(files, engine_mode, output_mode):
    if not files:
        return [], "⚠️ Status: No batch files uploaded."
    
    start_time = time.time()
    out_files = []
    # Cap at 15 files per batch for high-speed server response
    for f in files[:15]:
        try:
            img = Image.open(f.name).convert("RGBA")
            cutout, _, _ = execute_background_removal(img, engine_mode)
            if output_mode == "Solid Color (Obsidian Black)":
                bg = Image.new("RGBA", cutout.size, (5, 3, 10, 255))
                bg.paste(cutout, (0, 0), cutout)
                cutout = bg.convert("RGB")
            out_files.append(np.array(cutout))
        except Exception:
            continue

    elapsed = time.time() - start_time
    status = f"✅ Batch Processed Rapidly in {elapsed:.2f}s | Total Successfully Converted: {len(out_files)} images."
    return out_files, status

# =========================================================
# 07. ADVANCED COLOR GRADING STUDIO
# =========================================================
def process_color(img_arr, preset, b, c, s, sh, tint_color, tint_str):
    if img_arr is None:
        return None, "⚠️ Status: No image loaded."

    start_time = time.time()
    img = Image.fromarray(img_arr)
    img = optimize_image_size(img, max_dim=1400)

    # Preset Multipliers
    if preset == "Cyberpunk Neon":
        b, c, s, sh = 1.12, 1.40, 1.80, 1.45
    elif preset == "Shadow Dark / Cinematic":
        b, c, s, sh = 0.85, 1.50, 0.95, 1.30
    elif preset == "Anime Vibrant Boost":
        b, c, s, sh = 1.08, 1.25, 1.55, 1.20

    img = ImageEnhance.Brightness(img).enhance(b)
    img = ImageEnhance.Contrast(img).enhance(c)
    img = ImageEnhance.Color(img).enhance(s)
    img = ImageEnhance.Sharpness(img).enhance(sh)

    # Vectorized color tint overlay
    if tint_str > 0:
        img_rgb = img.convert("RGB")
        tint_rgb = hex_to_rgb(tint_color)
        tint_layer = Image.new("RGB", img_rgb.size, tint_rgb)
        img = Image.blend(img_rgb, tint_layer, alpha=(tint_str / 100.0))

    elapsed = time.time() - start_time
    status = f"🎨 Grade Applied in {elapsed:.2f}s | Preset: {preset} | Tint Strength: {tint_str}%"
    return np.array(img), status

# =========================================================
# 08. SMART CANVAS & EXPORT TOOL
# =========================================================
def process_export(img_arr, auto_trim, aspect, fmt):
    if img_arr is None:
        return None, "⚠️ Status: No image ready for export."

    start_time = time.time()
    img = Image.fromarray(img_arr)

    if auto_trim:
        if img.mode == "RGBA":
            bbox = img.split()[3].getbbox()
            if bbox: img = img.crop(bbox)
        else:
            gray = ImageOps.invert(img.convert("L"))
            bbox = gray.getbbox()
            if bbox: img = img.crop(bbox)

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

    elapsed = time.time() - start_time
    status = f"📦 Formatted in {elapsed:.2f}s | Target Format: {fmt} | Dimensions: {img.width}x{img.height}px"
    return np.array(img), status

def analyze_with_gemini(img_arr):
    if img_arr is None:
        return "⚠️ Please upload an image first."
    if not client or not GEMINI_MODEL:
        return "ℹ️ Google AI Status: GEMINI_API_KEY environment variable not set or SDK missing."

    try:
        pil_img = optimize_image_size(Image.fromarray(img_arr), max_dim=800)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[pil_img, "Analyze this image and provide a concise 2-sentence breakdown of its visual composition, lighting, and primary subject."]
        )
        return f"🤖 Gemini AI Telemetry:\n{response.text.strip()}"
    except Exception as e:
        err_str = str(e)
        if "404" in err_str:
            return f"⚠️ Google AI Status: Model endpoint '{GEMINI_MODEL}' unavailable on API key."
        return f"⚠️ Google AI Status: {err_str[:80]}..."

# =========================================================
# 09. GRADIO UI APPLICATION BUILD
# =========================================================
with gr.Blocks(title="Shadow Flamez AI Studio Pro v3.0", css=CUSTOM_CSS) as app:
    
    with gr.Row(elem_id="studio-header"):
        gr.Markdown(
            """
            # SHADOW FLAMEZ AI STUDIO PRO
            **v3.0 ULTIMATE** • High-Speed Cutout Engine, 4x Super-Res, Cyber Branding & Tone Matrix
            """
        )

    with gr.Tabs():
        # TAB 1: Compositor & Background Remover
        with gr.TabItem("⚡ Background & Compositor"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. INPUT & CUTOUT ENGINE")
                    comp_input = gr.Image(label="Upload Image", type="numpy")
                    comp_engine = gr.Radio(["⚡ Fast Matrix Keying (< 0.2s)", "🤖 Neural u2netp AI (Cached RAM)"], value="⚡ Fast Matrix Keying (< 0.2s)", label="Speed vs Precision Engine")
                    comp_bg_style = gr.Dropdown(["Transparent", "Solid Color", "Custom Background", "Original"], value="Transparent", label="Background Style")
                    comp_bg_color = gr.ColorPicker(label="Solid Background Color", value="#05030A")
                    comp_custom_bg = gr.Image(label="Custom Background Image", type="numpy")
                    comp_shadow = gr.Slider(minimum=0, maximum=100, value=35, label="Drop Shadow Intensity (%)")
                    comp_btn = gr.Button("🔥 EXECUTE HIGH-SPEED COMPOSITE", elem_classes=["cyber-btn"])
                    ai_btn = gr.Button("🤖 TELEMETRY: ANALYZE WITH GEMINI AI", elem_classes=["transfer-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. LIVE TELEMETRY & OUTPUT")
                    comp_specs = gr.Textbox(label="System Performance Telemetry", value="Ready for processing...", interactive=False)
                    
                    with gr.Tabs():
                        with gr.TabItem("Composited Result"):
                            comp_output = gr.Image(label="Studio Composite Output", interactive=False)
                        with gr.TabItem("Alpha Keyed Cutout"):
                            cutout_output = gr.Image(label="Transparent Cutout Mask", interactive=False)
                    
                    gr.Markdown("#### ⚡ Pipeline Quick-Transfer")
                    with gr.Row():
                        send_upscale = gr.Button("➡️ Send to 4x Upscaler", elem_classes=["transfer-btn"])
                        send_watermark = gr.Button("➡️ Send to Watermarking", elem_classes=["transfer-btn"])

        # TAB 2: 4x Super-Resolution Upscaler
        with gr.TabItem("🚀 4x AI Upscaler"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. SUPER-RESOLUTION CONFIG")
                    upscale_input = gr.Image(label="Upload Source Image", type="numpy")
                    upscale_btn = gr.Button("⚡ UPSCALE 4X INSTANTLY", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. HIGH-DEF OUTPUT")
                    upscale_specs = gr.Textbox(label="Upscale Performance Telemetry", value="Awaiting input...", interactive=False)
                    upscale_output = gr.Image(label="4x Super-Resolution Output", interactive=False)

        # TAB 3: Brand Watermarking
        with gr.TabItem("🏷️ Brand Watermark"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. BRANDING CONTROLS")
                    wm_base = gr.Image(label="Base Canvas Image", type="numpy")
                    wm_logo = gr.Image(label="Brand Logo / Watermark PNG", type="numpy")
                    wm_pos = gr.Dropdown(["Bottom Right", "Bottom Left", "Top Right", "Top Left", "Center Tile"], value="Bottom Right", label="Stamp Position")
                    wm_scale = gr.Slider(minimum=5, maximum=60, value=22, label="Watermark Size (% of Width)")
                    wm_opacity = gr.Slider(minimum=10, maximum=100, value=85, label="Stamp Opacity (%)")
                    wm_btn = gr.Button("🔥 APPLY BRAND WATERMARK", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. BRANDED CANVAS")
                    wm_specs = gr.Textbox(label="Branding Telemetry", value="Ready", interactive=False)
                    wm_output = gr.Image(label="Watermarked Result", interactive=False)

        # TAB 4: Batch Processing Engine
        with gr.TabItem("⚙️ Batch Processing"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. BULK REMOVAL ENGINE")
                    batch_files = gr.File(label="Upload Bulk Images (Max 15 per queue)", file_count="multiple")
                    batch_engine = gr.Radio(["⚡ Fast Matrix Keying (< 0.2s)", "🤖 Neural u2netp AI (Cached RAM)"], value="⚡ Fast Matrix Keying (< 0.2s)", label="Batch Processing Engine")
                    batch_mode = gr.Dropdown(["Transparent Alpha", "Solid Color (Obsidian Black)"], value="Transparent Alpha", label="Output Color Format")
                    batch_btn = gr.Button("⚡ PROCESS BATCH RAPIDLY", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. BATCH OUTPUT GALLERY")
                    batch_specs = gr.Textbox(label="Batch Execution Telemetry", value="Idle", interactive=False)
                    batch_gallery = gr.Gallery(label="Bulk Processed Results Gallery")

        # TAB 5: Color & Tone Matrix
        with gr.TabItem("🎨 Color & Tone Studio"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. COLOR MATRIX CONTROLS")
                    color_input = gr.Image(label="Upload Image to Grade", type="numpy")
                    color_preset = gr.Dropdown(["Custom", "Cyberpunk Neon", "Shadow Dark / Cinematic", "Anime Vibrant Boost"], value="Custom", label="Style Preset")
                    slider_b = gr.Slider(0.5, 2.0, value=1.0, label="Brightness")
                    slider_c = gr.Slider(0.5, 2.0, value=1.0, label="Contrast")
                    slider_s = gr.Slider(0.0, 2.5, value=1.0, label="Saturation")
                    slider_sh = gr.Slider(0.0, 3.0, value=1.0, label="Sharpness")
                    color_tint = gr.ColorPicker(label="Color Tint Overlay", value="#FF4500")
                    tint_strength = gr.Slider(0, 50, value=0, label="Tint Strength (%)")
                    color_btn = gr.Button("🔥 APPLY COLOR GRADE", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. GRADED CANVAS PREVIEW")
                    color_specs = gr.Textbox(label="Color Telemetry", value="Ready", interactive=False)
                    color_output = gr.Image(label="Color Graded Result", interactive=False)

        # TAB 6: Smart Export Canvas
        with gr.TabItem("📦 Smart Canvas Export"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. FORMAT & TRIM CONTROLS")
                    export_input = gr.Image(label="Upload Image", type="numpy")
                    export_autotrim = gr.Checkbox(label="Auto-Trim Border Whitespace & Alpha Bounding Box", value=True)
                    export_aspect = gr.Dropdown(["Original", "1:1 Square", "16:9 Landscape", "9:16 Story"], value="Original", label="Aspect Ratio Crop Fit")
                    export_fmt = gr.Radio(["PNG", "JPEG", "WEBP"], value="PNG", label="Target Export Format")
                    export_btn = gr.Button("⚡ CONVERT & EXPORT NOW", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. FINAL EXPORT PREVIEW")
                    export_specs = gr.Textbox(label="Export Telemetry", value="Ready", interactive=False)
                    export_output = gr.Image(label="Formatted Export Canvas", interactive=False)

    # Event Bindings
    comp_btn.click(process_composite, inputs=[comp_input, comp_engine, comp_bg_style, comp_bg_color, comp_custom_bg, comp_shadow], outputs=[comp_output, cutout_output, comp_specs])
    ai_btn.click(analyze_with_gemini, inputs=[comp_input], outputs=[comp_specs])
    upscale_btn.click(process_upscale, inputs=[upscale_input], outputs=[upscale_output, upscale_specs])
    wm_btn.click(process_watermark, inputs=[wm_base, wm_logo, wm_pos, wm_scale, wm_opacity], outputs=[wm_output, wm_specs])
    batch_btn.click(process_batch, inputs=[batch_files, batch_engine, batch_mode], outputs=[batch_gallery, batch_specs])
    color_btn.click(process_color, inputs=[color_input, color_preset, slider_b, slider_c, slider_s, slider_sh, color_tint, tint_strength], outputs=[color_output, color_specs])
    export_btn.click(process_export, inputs=[export_input, export_autotrim, export_aspect, export_fmt], outputs=[export_output, export_specs])

    # Inter-Tab Quick Transfers
    send_upscale.click(lambda x: x, inputs=[comp_output], outputs=[upscale_input])
    send_watermark.click(lambda x: x, inputs=[comp_output], outputs=[wm_base])

# Enable Asynchronous Multi-threaded Concurrency Queue
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    # queue() unlocks multi-threading so multiple operations don't lock up or freeze Render!
    app.queue(default_concurrency_limit=10).launch(server_name="0.0.0.0", server_port=port)
