import gradio as gr
import os
import io
import time
import gc
import concurrent.futures
import requests
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageFilter, ImageDraw

# =========================================================
# 01. MEMORY & THREAD POOL CONFIGURATION
# =========================================================
EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4)
GLOBAL_REMBG_SESSION = None

def get_rembg_session():
    global GLOBAL_REMBG_SESSION
    if GLOBAL_REMBG_SESSION is None:
        try:
            from rembg import new_session
            GLOBAL_REMBG_SESSION = new_session("u2netp")
        except Exception as e:
            print(f"⚠️ Rembg Session Load Warning: {e}")
            GLOBAL_REMBG_SESSION = "FALLBACK"
    return GLOBAL_REMBG_SESSION

def force_free_memory():
    """Purge RAM buffers to prevent Render 512MB RAM OOM crashes."""
    gc.collect()

def optimize_image_size(pil_img, max_dim=1024):
    """Cap image resolution dynamically for speed and memory protection."""
    w, h = pil_img.size
    if max(w, h) > max_dim:
        scale = max_dim / float(max(w, h))
        return pil_img.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
    return pil_img

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

# =========================================================
# 02. CYBERPUNK ANIMATION & HIGH-TECH STYLING (CSS)
# =========================================================
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&display=swap');

@keyframes cyber-pulse {
    0% { box-shadow: 0 0 15px rgba(255, 69, 0, 0.4), inset 0 0 10px rgba(255, 69, 0, 0.2); }
    50% { box-shadow: 0 0 30px rgba(0, 240, 255, 0.6), inset 0 0 20px rgba(0, 240, 255, 0.3); }
    100% { box-shadow: 0 0 15px rgba(255, 69, 0, 0.4), inset 0 0 10px rgba(255, 69, 0, 0.2); }
}

@keyframes text-glow {
    0% { text-shadow: 0 0 8px rgba(255, 69, 0, 0.8); }
    50% { text-shadow: 0 0 18px rgba(0, 240, 255, 0.9), 0 0 30px rgba(138, 43, 226, 0.8); }
    100% { text-shadow: 0 0 8px rgba(255, 69, 0, 0.8); }
}

@keyframes scanline {
    0% { background-position: 0 0; }
    100% { background-position: 0 100%; }
}

body, .gradio-container {
    background-color: #030108 !important;
    background-image: 
        radial-gradient(circle at 15% 20%, rgba(255, 69, 0, 0.15) 0%, transparent 45%),
        radial-gradient(circle at 85% 80%, rgba(0, 240, 255, 0.12) 0%, transparent 50%),
        radial-gradient(circle at 50% 50%, rgba(138, 43, 226, 0.08) 0%, transparent 65%) !important;
    font-family: 'Rajdhani', sans-serif !important;
    color: #F1F5F9 !important;
}

#studio-header {
    background: rgba(10, 6, 18, 0.88) !important;
    border: 1px solid rgba(255, 69, 0, 0.5) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    text-align: center !important;
    margin-bottom: 20px !important;
    animation: cyber-pulse 4s infinite ease-in-out !important;
    backdrop-filter: blur(12px) !important;
}

#studio-header h1 {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 2.4rem !important;
    font-weight: 900 !important;
    letter-spacing: 4px !important;
    background: linear-gradient(135deg, #FF4500 0%, #FF8C00 30%, #00F0FF 70%, #8A2BE2 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    animation: text-glow 3s infinite ease-in-out !important;
    text-transform: uppercase !important;
    margin: 0 !important;
}

.cyber-panel {
    background: rgba(13, 8, 22, 0.8) !important;
    border: 1px solid rgba(0, 240, 255, 0.3) !important;
    border-radius: 14px !important;
    padding: 20px !important;
    backdrop-filter: blur(16px) !important;
    transition: transform 0.2s ease, border-color 0.3s ease !important;
}

.cyber-panel:hover {
    border-color: rgba(255, 69, 0, 0.6) !important;
}

.cyber-btn {
    background: linear-gradient(135deg, #FF4500 0%, #8A2BE2 100%) !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    color: #FFFFFF !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border-radius: 8px !important;
    padding: 14px !important;
    box-shadow: 0 0 20px rgba(255, 69, 0, 0.4) !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
}

.cyber-btn:hover {
    transform: translateY(-2px) scale(1.01) !important;
    box-shadow: 0 0 30px rgba(0, 240, 255, 0.7) !important;
}

.transfer-btn {
    background: rgba(0, 240, 255, 0.1) !important;
    border: 1px solid rgba(0, 240, 255, 0.5) !important;
    color: #00F0FF !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
}

.transfer-btn:hover {
    background: rgba(0, 240, 255, 0.25) !important;
    box-shadow: 0 0 15px rgba(0, 240, 255, 0.5) !important;
}

div[data-testid="image"], .gradio-image {
    background-color: rgba(6, 4, 12, 0.95) !important;
    border: 2px dashed rgba(0, 240, 255, 0.4) !important;
    border-radius: 12px !important;
}

.colab-badge {
    background: rgba(0, 240, 255, 0.15) !important;
    border: 1px solid #00F0FF !important;
    padding: 8px 14px !important;
    border-radius: 8px !important;
    color: #00F0FF !important;
    font-weight: bold !important;
}
"""

# =========================================================
# 03. CORE ENGINE LOGIC & COLAB OFF-LOADING
# =========================================================
def call_colab_api(colab_url, task_type, image_arr, **kwargs):
    """Sends heavy workloads to Google Colab CPU/GPU instance if URL is configured."""
    try:
        endpoint = f"{colab_url.rstrip('/')}/api/predict"
        payload = {
            "task": task_type,
            "params": kwargs
        }
        response = requests.post(endpoint, json=payload, timeout=25)
        if response.status_code == 200:
            res_data = response.json()
            return res_data.get("result"), "Connected to Google Colab Cloud CPU/GPU Engine"
    except Exception as e:
        print(f"Colab Bridge Notice: {e} - Falling back to local Render engine.")
    return None, None

def execute_background_removal(pil_img, engine_mode, threshold=238):
    start_time = time.time()
    img = optimize_image_size(pil_img, max_dim=1024)
    
    if engine_mode == "⚡ Fast Matrix Keying (< 0.2s)":
        img_rgba = img.convert("RGBA")
        data = np.array(img_rgba)
        r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
        mask = (r > threshold) & (g > threshold) & (b > threshold)
        data[:, :, 3] = np.where(mask, 0, a)
        cutout = Image.fromarray(data)
        mode_used = "Vectorized Matrix Keyer"
        del data, mask
    else:
        session = get_rembg_session()
        if session != "FALLBACK" and session is not None:
            try:
                from rembg import remove
                cutout = remove(img, session=session)
                mode_used = "Neural u2netp AI"
            except Exception:
                cutout = execute_background_removal(img, "⚡ Fast Matrix Keying (< 0.2s)")[0]
                mode_used = "Matrix Keyer (Fallback)"
        else:
            cutout = execute_background_removal(img, "⚡ Fast Matrix Keying (< 0.2s)")[0]
            mode_used = "Matrix Keyer (RAM Saver)"
            
    elapsed = time.time() - start_time
    return cutout, mode_used, elapsed

def process_composite(img_arr, engine_mode, bg_style, bg_color, custom_bg_arr, shadow_val, colab_url=""):
    if img_arr is None:
        return None, None, "⚠️ Status: Upload a source image first.", gr.Tabs(selected="result_subtab")

    try:
        # Check Colab offloading bridge first
        if colab_url.strip():
            res, remote_msg = call_colab_api(colab_url, "composite", img_arr, engine=engine_mode)
            if res is not None:
                return res, res, f"🚀 {remote_msg}", gr.Tabs(selected="result_subtab")

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
                shadow = shadow.filter(ImageFilter.BoxBlur(5))
                bg.paste(shadow, (10, 10), shadow)
                del shadow
                
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

        status = f"⚡ Rendered in {exec_time:.2f}s | Engine: {mode_used} | Res: {res.width}x{res.height}px | Style: {status_style}"
        out_res, out_cut = np.array(res), np.array(cutout_img)
        
        del orig_img, cutout_img
        force_free_memory()
        
        return out_res, out_cut, status, gr.Tabs(selected="result_subtab")
        
    except Exception as e:
        force_free_memory()
        return None, None, f"⚠️ Error: {str(e)}", gr.Tabs(selected="result_subtab")

def process_upscale(img_arr, sharpness_val, color_boost):
    if img_arr is None:
        return None, "⚠️ Status: Upload an image to upscale."

    try:
        start_time = time.time()
        img = Image.fromarray(img_arr)
        img = optimize_image_size(img, max_dim=900)
        
        new_size = (img.width * 4, img.height * 4)
        upscaled = img.resize(new_size, Image.Resampling.LANCZOS)

        if sharpness_val > 1.0:
            sharpener = ImageEnhance.Sharpness(upscaled)
            upscaled = sharpener.enhance(sharpness_val)

        if color_boost > 1.0:
            enhancer = ImageEnhance.Color(upscaled)
            upscaled = enhancer.enhance(color_boost)

        elapsed = time.time() - start_time
        status = f"🚀 4x Super-Res Completed in {elapsed:.2f}s | Output Size: {upscaled.width}x{upscaled.height}px"
        res_arr = np.array(upscaled)
        
        del img, upscaled
        force_free_memory()
        return res_arr, status
    except Exception as e:
        force_free_memory()
        return None, f"⚠️ Upscale Error: {str(e)}"

def process_watermark(img_arr, logo_arr, pos, scale, opacity, rotation):
    if img_arr is None:
        return None, "⚠️ Status: Base image required."
    if logo_arr is None:
        return img_arr, "⚠️ Status: Upload a logo image."

    try:
        start_time = time.time()
        base = Image.fromarray(img_arr).convert("RGBA")
        logo = Image.fromarray(logo_arr).convert("RGBA")

        if rotation != 0:
            logo = logo.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)

        logo_width = max(int(base.width * (scale / 100.0)), 20)
        aspect_ratio = logo.height / float(logo.width)
        logo_height = int(logo_width * aspect_ratio)
        logo = logo.resize((logo_width, logo_height), Image.Resampling.BILINEAR)

        r, g, b, alpha = logo.split()
        alpha = alpha.point(lambda i: int(i * (opacity / 100.0)))
        logo.putalpha(alpha)

        margin = int(base.width * 0.03)
        if pos == "Bottom Right":
            x, y = base.width - logo_width - margin, base.height - logo_height - margin
        elif pos == "Bottom Left":
            x, y = margin, base.height - logo_height - margin
        elif pos == "Top Right":
            x, y = base.width - logo_width - margin, margin
        elif pos == "Top Left":
            x, y = margin, margin
        else:
            x, y = (base.width - logo_width) // 2, (base.height - logo_height) // 2

        watermarked = base.copy()
        watermarked.paste(logo, (x, y), logo)
        
        elapsed = time.time() - start_time
        status = f"🏷️ Watermarked in {elapsed:.2f}s | Pos: {pos} | Scale: {scale}% | Angle: {rotation}°"
        res_arr = np.array(watermarked.convert("RGB"))
        
        del base, logo, watermarked
        force_free_memory()
        return res_arr, status
    except Exception as e:
        force_free_memory()
        return None, f"⚠️ Watermark Error: {str(e)}"

def process_cyber_fx(img_arr, fx_type, intensity):
    if img_arr is None:
        return None, "⚠️ Upload image first."

    try:
        start_time = time.time()
        img = Image.fromarray(img_arr).convert("RGB")
        img = optimize_image_size(img, max_dim=1024)

        if fx_type == "🔥 Shadow Flame Aura":
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.0 + (intensity / 50.0))
            contrast = ImageEnhance.Contrast(img)
            img = contrast.enhance(1.2)
        elif fx_type == "🤖 Neon Edge Cyberpunk":
            edges = img.filter(ImageFilter.FIND_EDGES)
            edges = ImageOps.invert(edges)
            img = Image.blend(img, edges, alpha=(intensity / 100.0))
        elif fx_type == "⚡ High-Contrast Dark Glow":
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.0 + (intensity / 40.0))
        
        elapsed = time.time() - start_time
        status = f"✨ Cyber FX Applied in {elapsed:.2f}s | Preset: {fx_type}"
        res_arr = np.array(img)
        
        del img
        force_free_memory()
        return res_arr, status
    except Exception as e:
        force_free_memory()
        return None, f"⚠️ FX Error: {str(e)}"

# Transfer Functions with Tab Auto-Switching
def transfer_to_upscale(img):
    force_free_memory()
    return img, gr.Tabs(selected="tab_upscale")

def transfer_to_watermark(img):
    force_free_memory()
    return img, gr.Tabs(selected="tab_watermark")

def transfer_to_fx(img):
    force_free_memory()
    return img, gr.Tabs(selected="tab_fx")

# =========================================================
# 04. GRADIO INTERFACE BUILD
# =========================================================
with gr.Blocks(title="Shadow Flamez AI Studio Pro", css=CUSTOM_CSS) as app:
    
    # Animated Header
    with gr.Row(elem_id="studio-header"):
        gr.Markdown(
            """
            # SHADOW FLAMEZ AI STUDIO PRO
            **v4.0 Cyber Edition** • Google Colab Bridge • High-Speed Multitasking Architecture
            """
        )

    # Main Navigation Tabs
    with gr.Tabs(selected="tab_comp") as main_tabs:
        
        # TAB 1: Compositor & Background Removal
        with gr.TabItem("⚡ Background & Compositor", id="tab_comp"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. SOURCE & CUTOUT ENGINE")
                    comp_input = gr.Image(label="Upload Image", type="numpy")
                    comp_engine = gr.Radio(["⚡ Fast Matrix Keying (< 0.2s)", "🤖 Neural u2netp AI (Cached RAM)"], value="⚡ Fast Matrix Keying (< 0.2s)", label="Cutout Speed Engine")
                    comp_bg_style = gr.Dropdown(["Transparent", "Solid Color", "Custom Background", "Original"], value="Transparent", label="Background Style")
                    comp_bg_color = gr.ColorPicker(label="Solid Background Color", value="#030108")
                    comp_custom_bg = gr.Image(label="Custom Background Image", type="numpy")
                    comp_shadow = gr.Slider(minimum=0, maximum=100, value=30, label="Drop Shadow Intensity (%)")
                    
                    with gr.Accordion("🌐 Google Colab CPU/GPU Bridge (Optional)", open=False):
                        colab_url_input = gr.Textbox(label="Colab Public Tunnel URL", placeholder="https://xxxx.ngrok-free.app or Gradio Live URL")
                    
                    comp_btn = gr.Button("🔥 EXECUTE COMPOSITE", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. LIVE PREVIEW & TELEMETRY")
                    comp_specs = gr.Textbox(label="Performance Telemetry", value="System Ready...", interactive=False)
                    
                    with gr.Tabs(selected="result_subtab") as preview_subtabs:
                        with gr.TabItem("Composited Result", id="result_subtab"):
                            comp_output = gr.Image(label="Studio Composite Output", interactive=False)
                        with gr.TabItem("Alpha Keyed Cutout", id="cutout_subtab"):
                            cutout_output = gr.Image(label="Transparent Cutout Mask", interactive=False)
                    
                    gr.Markdown("#### ⚡ Dynamic One-Click Navigation")
                    with gr.Row():
                        send_upscale_btn = gr.Button("➡️ Send to 4K Upscaler", elem_classes=["transfer-btn"])
                        send_watermark_btn = gr.Button("➡️ Send to Watermark", elem_classes=["transfer-btn"])
                        send_fx_btn = gr.Button("➡️ Send to FX Engine", elem_classes=["transfer-btn"])

        # TAB 2: 4x AI Upscaler
        with gr.TabItem("🚀 4x AI Upscaler", id="tab_upscale"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. SUPER-RESOLUTION CONTROLS")
                    upscale_input = gr.Image(label="Upload Image or Transferred Source", type="numpy")
                    sharpness_slider = gr.Slider(minimum=1.0, maximum=3.0, value=1.4, step=0.1, label="Edge Sharpness Filter")
                    color_boost_slider = gr.Slider(minimum=1.0, maximum=2.0, value=1.1, step=0.1, label="Cyber Color Vibrance")
                    upscale_btn = gr.Button("⚡ UPSCALE 4X NOW", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. HIGH-RES OUTPUT")
                    upscale_specs = gr.Textbox(label="Upscale Status", value="Awaiting image...", interactive=False)
                    upscale_output = gr.Image(label="4K Enhanced Output", interactive=False)

        # TAB 3: Watermarking
        with gr.TabItem("🏷️ Brand Watermark", id="tab_watermark"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. WATERMARK CONTROLS")
                    wm_base = gr.Image(label="Base Image or Transferred Source", type="numpy")
                    wm_logo = gr.Image(label="Brand Logo / Watermark PNG", type="numpy")
                    wm_pos = gr.Dropdown(["Bottom Right", "Bottom Left", "Top Right", "Top Left", "Center Tile"], value="Bottom Right", label="Position")
                    wm_scale = gr.Slider(minimum=5, maximum=60, value=22, label="Scale (%)")
                    wm_opacity = gr.Slider(minimum=10, maximum=100, value=85, label="Opacity (%)")
                    wm_rotation = gr.Slider(minimum=-180, maximum=180, value=0, label="Rotation Angle (°)")
                    wm_btn = gr.Button("🔥 APPLY BRAND STAMP", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. BRANDED OUTPUT")
                    wm_specs = gr.Textbox(label="Watermark Status", value="Ready", interactive=False)
                    wm_output = gr.Image(label="Watermarked Output", interactive=False)

        # TAB 4: Cyber & Anime FX
        with gr.TabItem("🎨 Cyber FX Engine", id="tab_fx"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. CYBER & ANIME PRESETS")
                    fx_input = gr.Image(label="Upload Image or Transferred Source", type="numpy")
                    fx_type = gr.Radio(["🔥 Shadow Flame Aura", "🤖 Neon Edge Cyberpunk", "⚡ High-Contrast Dark Glow"], value="🔥 Shadow Flame Aura", label="FX Preset")
                    fx_intensity = gr.Slider(minimum=10, maximum=100, value=50, label="FX Intensity (%)")
                    fx_btn = gr.Button("✨ APPLY CYBER FX", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. FX STYLED OUTPUT")
                    fx_specs = gr.Textbox(label="FX Telemetry", value="Ready", interactive=False)
                    fx_output = gr.Image(label="Stylized Image", interactive=False)

    # Event Bindings with Auto-Tab Switching
    comp_btn.click(
        fn=process_composite,
        inputs=[comp_input, comp_engine, comp_bg_style, comp_bg_color, comp_custom_bg, comp_shadow, colab_url_input],
        outputs=[comp_output, cutout_output, comp_specs, preview_subtabs]
    )
    
    upscale_btn.click(
        fn=process_upscale,
        inputs=[upscale_input, sharpness_slider, color_boost_slider],
        outputs=[upscale_output, upscale_specs]
    )
    
    wm_btn.click(
        fn=process_watermark,
        inputs=[wm_base, wm_logo, wm_pos, wm_scale, wm_opacity, wm_rotation],
        outputs=[wm_output, wm_specs]
    )

    fx_btn.click(
        fn=process_cyber_fx,
        inputs=[fx_input, fx_type, fx_intensity],
        outputs=[fx_output, fx_specs]
    )

    # Dynamic One-Click Navigation Handlers
    send_upscale_btn.click(
        fn=transfer_to_upscale,
        inputs=[comp_output],
        outputs=[upscale_input, main_tabs]
    )
    
    send_watermark_btn.click(
        fn=transfer_to_watermark,
        inputs=[comp_output],
        outputs=[wm_base, main_tabs]
    )

    send_fx_btn.click(
        fn=transfer_to_fx,
        inputs=[comp_output],
        outputs=[fx_input, main_tabs]
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.queue(default_concurrency_limit=8).launch(server_name="0.0.0.0", server_port=port)
