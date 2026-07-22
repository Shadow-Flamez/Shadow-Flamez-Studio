import gradio as gr
import os
import time
import gc
import concurrent.futures
import requests
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageFilter, ImageDraw, ImageFont

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
    if not hex_str:
        return (0, 0, 0)
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
"""

# =========================================================
# 03. CORE PROCESSING ENGINES
# =========================================================

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

# FEATURE 1: COMPOSITOR (Attribute Bug Fixed)
def process_composite(img_arr, engine_mode, bg_style, bg_color, custom_bg_arr, shadow_val, colab_url=""):
    if img_arr is None:
        return None, None, "⚠️ Status: Upload a source image first.", gr.Tabs(selected="result_subtab")

    try:
        # BUG FIX: Safe string check for NoneType
        if colab_url and isinstance(colab_url, str) and colab_url.strip():
            try:
                endpoint = f"{colab_url.strip().rstrip('/')}/api/predict"
                payload = {"task": "composite", "params": {"engine": engine_mode}}
                response = requests.post(endpoint, json=payload, timeout=20)
                if response.status_code == 200:
                    res_data = response.json()
                    res = res_data.get("result")
                    return res, res, "🚀 Processed via Remote Colab Instance", gr.Tabs(selected="result_subtab")
            except Exception as bridge_err:
                print(f"Colab Bridge Notice: {bridge_err} - Processing on local Render container.")

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

# FEATURE 2: 4X AI UPSCALER
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

# FEATURE 3: BRAND WATERMARK
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

# FEATURE 4: CYBER FX ENGINE
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

# =========================================================
# NEW FEATURES (05 - 10)
# =========================================================

# FEATURE 5: NEON OUTER GLOW & ENERGY AURA
def process_energy_aura(img_arr, glow_color_hex, glow_radius, glow_blur):
    if img_arr is None:
        return None, "⚠️ Please upload a cutout or image."
    try:
        start_time = time.time()
        img = Image.fromarray(img_arr).convert("RGBA")
        img = optimize_image_size(img, max_dim=1024)
        
        # Extract alpha channel
        alpha = img.split()[3]
        
        # Create solid color image for glow
        glow_color = hex_to_rgb(glow_color_hex)
        glow_mask = alpha.filter(ImageFilter.MaxFilter(int(glow_radius)))
        glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(int(glow_blur)))
        
        glow_img = Image.new("RGBA", img.size, glow_color + (255,))
        glow_img.putalpha(glow_mask)
        
        # Paste subject over glow
        combined = Image.new("RGBA", img.size, (0, 0, 0, 0))
        combined.paste(glow_img, (0,0), glow_img)
        combined.paste(img, (0,0), img)
        
        elapsed = time.time() - start_time
        res_arr = np.array(combined)
        del img, glow_mask, glow_img, combined
        force_free_memory()
        return res_arr, f"🔥 Aura Generated in {elapsed:.2f}s | Color: {glow_color_hex}"
    except Exception as e:
        force_free_memory()
        return None, f"⚠️ Aura Error: {str(e)}"

# FEATURE 6: SOCIAL CANVAS & ASPECT RATIO RESIZER
def process_canvas_resize(img_arr, ratio, padding_color, blur_bg):
    if img_arr is None:
        return None, "⚠️ Upload an image."
    try:
        start_time = time.time()
        img = Image.fromarray(img_arr).convert("RGB")
        w, h = img.size
        
        aspect_dict = {
            "1:1 Square (Insta/Profile)": (1080, 1080),
            "16:9 Landscape (YouTube/Banner)": (1920, 1080),
            "9:16 Portrait (Reels/TikTok)": (1080, 1920),
            "4:5 Portrait (Insta Post)": (1080, 1350)
        }
        
        target_w, target_h = aspect_dict.get(ratio, (1080, 1080))
        
        if blur_bg:
            canvas = img.resize((target_w, target_h), Image.Resampling.BILINEAR)
            canvas = canvas.filter(ImageFilter.GaussianBlur(25))
        else:
            bg_rgb = hex_to_rgb(padding_color)
            canvas = Image.new("RGB", (target_w, target_h), bg_rgb)
            
        # Scale subject proportionally into canvas
        scale = min(target_w / float(w), target_h / float(h))
        new_w, new_h = int(w * scale), int(h * scale)
        resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        offset_x = (target_w - new_w) // 2
        offset_y = (target_h - new_h) // 2
        canvas.paste(resized_img, (offset_x, offset_y))
        
        elapsed = time.time() - start_time
        res_arr = np.array(canvas)
        del img, canvas, resized_img
        force_free_memory()
        return res_arr, f"📐 Canvas Formatted in {elapsed:.2f}s | Target: {target_w}x{target_h}px"
    except Exception as e:
        force_free_memory()
        return None, f"⚠️ Canvas Error: {str(e)}"

# FEATURE 7: CYBER GLITCH & CHROMATIC ABERRATION
def process_glitch_effect(img_arr, shift_pixels, scanlines):
    if img_arr is None:
        return None, "⚠️ Upload an image."
    try:
        start_time = time.time()
        img = Image.fromarray(img_arr).convert("RGB")
        img = optimize_image_size(img, max_dim=1024)
        
        arr = np.array(img)
        r = arr[:, :, 0]
        g = arr[:, :, 1]
        b = arr[:, :, 2]
        
        # Horizontal Chromatic Shift
        r_shifted = np.roll(r, int(shift_pixels), axis=1)
        b_shifted = np.roll(b, -int(shift_pixels), axis=1)
        
        glitch_arr = np.stack([r_shifted, g, b_shifted], axis=2)
        glitch_img = Image.fromarray(glitch_arr)
        
        if scanlines:
            draw = ImageDraw.Draw(glitch_img)
            for y in range(0, glitch_img.height, 4):
                draw.line([(0, y), (glitch_img.width, y)], fill=(0, 0, 0, 100), width=1)
                
        elapsed = time.time() - start_time
        res_arr = np.array(glitch_img)
        del img, arr, r, g, b, glitch_img
        force_free_memory()
        return res_arr, f"🎞️ Cyber Glitch Applied in {elapsed:.2f}s | Shift: {shift_pixels}px"
    except Exception as e:
        force_free_memory()
        return None, f"⚠️ Glitch Error: {str(e)}"

# FEATURE 8: CINEMATIC LIGHTING & VIGNETTE
def process_cinematic_vignette(img_arr, vignette_strength, warm_cool_tint):
    if img_arr is None:
        return None, "⚠️ Upload an image."
    try:
        start_time = time.time()
        img = Image.fromarray(img_arr).convert("RGB")
        img = optimize_image_size(img, max_dim=1024)
        
        # Color temperature tinting
        if warm_cool_tint != 0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1)
            arr = np.array(img, dtype=np.float32)
            if warm_cool_tint > 0: # Warm / Fire
                arr[:, :, 0] = np.clip(arr[:, :, 0] + warm_cool_tint * 0.5, 0, 255)
            else: # Cool / Cyber
                arr[:, :, 2] = np.clip(arr[:, :, 2] - warm_cool_tint * 0.5, 0, 255)
            img = Image.fromarray(arr.astype(np.uint8))
            
        # Vignette Mask creation
        w, h = img.size
        x = np.linspace(-1, 1, w)
        y = np.linspace(-1, 1, h)
        X, Y = np.meshgrid(x, y)
        radius = np.sqrt(X**2 + Y**2)
        vignette_mask = 1 - np.clip(radius * (vignette_strength / 100.0), 0, 1)
        vignette_mask = np.stack([vignette_mask]*3, axis=2)
        
        img_arr_val = np.array(img, dtype=np.float32) * vignette_mask
        res_img = Image.fromarray(np.clip(img_arr_val, 0, 255).astype(np.uint8))
        
        elapsed = time.time() - start_time
        res_arr = np.array(res_img)
        del img, res_img
        force_free_memory()
        return res_arr, f"🎭 Cinematic Lighting Rendered in {elapsed:.2f}s"
    except Exception as e:
        force_free_memory()
        return None, f"⚠️ Lighting Error: {str(e)}"

# FEATURE 9: TYPOGRAPHY & BANNER GENERATOR
def process_text_overlay(img_arr, header_text, sub_text, text_color, bg_plate_opacity, text_pos):
    if img_arr is None:
        return None, "⚠️ Upload an image."
    try:
        start_time = time.time()
        img = Image.fromarray(img_arr).convert("RGBA")
        img = optimize_image_size(img, max_dim=1024)
        
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        font_size = max(24, int(img.width * 0.05))
        sub_font_size = int(font_size * 0.6)
        
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
            sub_font = ImageFont.truetype("DejaVuSans.ttf", sub_font_size)
        except Exception:
            font = ImageFont.load_default()
            sub_font = font
            
        tc_rgb = hex_to_rgb(text_color)
        
        # Positions
        y_pos = int(img.height * 0.15) if text_pos == "Top Banner" else int(img.height * 0.75)
        
        # Background plate banner
        if bg_plate_opacity > 0:
            plate_h = font_size + sub_font_size + 40
            plate_box = [0, y_pos - 15, img.width, y_pos + plate_h]
            draw.rectangle(plate_box, fill=(5, 2, 12, int(255 * (bg_plate_opacity / 100.0))))
            
        draw.text((30, y_pos), header_text.upper(), fill=tc_rgb + (255,), font=font)
        draw.text((32, y_pos + font_size + 8), sub_text, fill=(200, 220, 255, 230), font=sub_font)
        
        combined = Image.alpha_composite(img, overlay)
        elapsed = time.time() - start_time
        res_arr = np.array(combined.convert("RGB"))
        del img, overlay, combined
        force_free_memory()
        return res_arr, f"✏️ Banner Stamped in {elapsed:.2f}s | Title: {header_text[:15]}..."
    except Exception as e:
        force_free_memory()
        return None, f"⚠️ Text Overlay Error: {str(e)}"

# FEATURE 10: CYBER DUOTONE GRADIENT MAPPER
def process_duotone_palette(img_arr, color1_hex, color2_hex):
    if img_arr is None:
        return None, "⚠️ Upload an image."
    try:
        start_time = time.time()
        img = Image.fromarray(img_arr).convert("L") # Gray scale
        img = optimize_image_size(img, max_dim=1024)
        
        c1 = np.array(hex_to_rgb(color1_hex), dtype=np.float32)
        c2 = np.array(hex_to_rgb(color2_hex), dtype=np.float32)
        
        gray = np.array(img, dtype=np.float32) / 255.0
        duotone = np.zeros((img.height, img.width, 3), dtype=np.uint8)
        
        for ch in range(3):
            duotone[:, :, ch] = np.clip((1 - gray) * c1[ch] + gray * c2[ch], 0, 255).astype(np.uint8)
            
        elapsed = time.time() - start_time
        res_arr = duotone
        del img
        force_free_memory()
        return res_arr, f"🎨 Cyber Duotone Mapped in {elapsed:.2f}s | {color1_hex} -> {color2_hex}"
    except Exception as e:
        force_free_memory()
        return None, f"⚠️ Duotone Error: {str(e)}"


# Transfer Functions with Auto Tab Switches
def transfer_to_tab(img, target_tab_id):
    force_free_memory()
    return img, gr.Tabs(selected=target_tab_id)

# =========================================================
# 04. GRADIO INTERFACE BUILD
# =========================================================
with gr.Blocks(title="Shadow Flamez AI Studio Pro v5", css=CUSTOM_CSS) as app:
    
    # Animated Header
    with gr.Row(elem_id="studio-header"):
        gr.Markdown(
            """
            # SHADOW FLAMEZ AI STUDIO PRO
            **v5.0 Render Edition** • High-Speed Multitasking Suite • 10 Cyber Engines
            """
        )

    # Main Navigation Tabs
    with gr.Tabs(selected="tab_comp") as main_tabs:
        
        # TOOL 1: Compositor & Background Removal
        with gr.TabItem("⚡ Background & Cutout", id="tab_comp"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. SOURCE & CUTOUT ENGINE")
                    comp_input = gr.Image(label="Upload Image", type="numpy")
                    comp_engine = gr.Radio(["⚡ Fast Matrix Keying (< 0.2s)", "🤖 Neural u2netp AI (Cached RAM)"], value="⚡ Fast Matrix Keying (< 0.2s)", label="Cutout Speed Engine")
                    comp_bg_style = gr.Dropdown(["Transparent", "Solid Color", "Custom Background", "Original"], value="Transparent", label="Background Style")
                    comp_bg_color = gr.ColorPicker(label="Solid Background Color", value="#030108")
                    comp_custom_bg = gr.Image(label="Custom Background Image", type="numpy")
                    comp_shadow = gr.Slider(minimum=0, maximum=100, value=30, label="Drop Shadow Intensity (%)")
                    
                    with gr.Accordion("🌐 Optional Colab Tunnel URL (Leave Empty for Render)", open=False):
                        colab_url_input = gr.Textbox(label="Colab Public Tunnel URL", value="", placeholder="https://xxxx.ngrok-free.app")
                    
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
                        send_upscale_btn = gr.Button("➡️ 4K Upscaler", elem_classes=["transfer-btn"])
                        send_aura_btn = gr.Button("➡️ Neon Aura", elem_classes=["transfer-btn"])
                        send_watermark_btn = gr.Button("➡️ Watermark", elem_classes=["transfer-btn"])

        # TOOL 2: 4x AI Upscaler
        with gr.TabItem("🚀 4x Upscaler", id="tab_upscale"):
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

        # TOOL 3: Brand Watermark
        with gr.TabItem("🏷️ Watermark Studio", id="tab_watermark"):
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

        # TOOL 4: Cyber FX Engine
        with gr.TabItem("🎨 Cyber FX", id="tab_fx"):
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

        # TOOL 5: Neon Energy Aura (NEW)
        with gr.TabItem("🔥 Neon Energy Aura", id="tab_aura"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. AURA STROKE ENGINE")
                    aura_input = gr.Image(label="Cutout PNG (With Transparency)", type="numpy")
                    aura_color = gr.ColorPicker(label="Aura Glow Color", value="#FF4500")
                    aura_radius = gr.Slider(minimum=2, maximum=40, value=15, label="Aura Radius (px)")
                    aura_blur = gr.Slider(minimum=1, maximum=30, value=10, label="Glow Softness Blur")
                    aura_btn = gr.Button("🔥 GENERATE NEON AURA", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. AURA OUTPUT")
                    aura_specs = gr.Textbox(label="Aura Status", value="Ready", interactive=False)
                    aura_output = gr.Image(label="Subject with Glowing Aura", interactive=False)

        # TOOL 6: Canvas & Social Aspect Ratio (NEW)
        with gr.TabItem("📐 Social Canvas", id="tab_canvas"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. ASPECT RATIO & FRAMING")
                    canvas_input = gr.Image(label="Upload Image", type="numpy")
                    canvas_ratio = gr.Dropdown(["1:1 Square (Insta/Profile)", "16:9 Landscape (YouTube/Banner)", "9:16 Portrait (Reels/TikTok)", "4:5 Portrait (Insta Post)"], value="16:9 Landscape (YouTube/Banner)", label="Target Aspect Ratio")
                    canvas_blur = gr.Checkbox(label="Use Blurred Image Background", value=True)
                    canvas_bg_color = gr.ColorPicker(label="Padding Color (If Blur Off)", value="#05020c")
                    canvas_btn = gr.Button("📐 FORMAT CANVAS", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. CANVAS OUTPUT")
                    canvas_specs = gr.Textbox(label="Canvas Status", value="Ready", interactive=False)
                    canvas_output = gr.Image(label="Formatted Aspect Ratio Image", interactive=False)

        # TOOL 7: Cyber Glitch & Chromatic Shift (NEW)
        with gr.TabItem("🎞️ Cyber Glitch", id="tab_glitch"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. CHROMATIC SHIFT CONTROLS")
                    glitch_input = gr.Image(label="Upload Image", type="numpy")
                    glitch_shift = gr.Slider(minimum=1, maximum=25, value=8, label="RGB Split Shift (px)")
                    glitch_scanlines = gr.Checkbox(label="Overlay CRT Scanlines", value=True)
                    glitch_btn = gr.Button("🎞️ APPLY CYBER GLITCH", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. GLITCH OUTPUT")
                    glitch_specs = gr.Textbox(label="Glitch Status", value="Ready", interactive=False)
                    glitch_output = gr.Image(label="Glitch Distortion Output", interactive=False)

        # TOOL 8: Cinematic Lighting & Vignette (NEW)
        with gr.TabItem("🎭 Cinematic Lighting", id="tab_lighting"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. ATMOSPHERIC LIGHTING")
                    lighting_input = gr.Image(label="Upload Image", type="numpy")
                    vignette_slider = gr.Slider(minimum=0, maximum=100, value=65, label="Vignette Frame Shadow (%)")
                    tint_slider = gr.Slider(minimum=-50, maximum=50, value=15, label="Color Tint (Cool Cyber ⬅️ 0 ➡️ Warm Flame)")
                    lighting_btn = gr.Button("🎭 APPLY LIGHTING", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. LIGHTING OUTPUT")
                    lighting_specs = gr.Textbox(label="Lighting Status", value="Ready", interactive=False)
                    lighting_output = gr.Image(label="Cinematic Mood Result", interactive=False)

        # TOOL 9: Banner & Typography Generator (NEW)
        with gr.TabItem("✏️ Banner Text", id="tab_text"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. TYPOGRAPHY CONTROLS")
                    text_input = gr.Image(label="Upload Image", type="numpy")
                    text_header = gr.Textbox(label="Header Title", value="SHADOW FLAMEZ")
                    text_sub = gr.Textbox(label="Subtitle / Tagline", value="PRO NEURAL STUDIO EDITION")
                    text_color = gr.ColorPicker(label="Title Font Color", value="#00F0FF")
                    text_plate_op = gr.Slider(minimum=0, maximum=100, value=75, label="Dark Backplate Opacity (%)")
                    text_pos = gr.Radio(["Top Banner", "Bottom Banner"], value="Bottom Banner", label="Banner Position")
                    text_btn = gr.Button("✏️ STAMP BANNER TEXT", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. TYPOGRAPHY OUTPUT")
                    text_specs = gr.Textbox(label="Banner Status", value="Ready", interactive=False)
                    text_output = gr.Image(label="Banner Output", interactive=False)

        # TOOL 10: Cyber Duotone Gradient Mapper (NEW)
        with gr.TabItem("🎨 Duotone Palette", id="tab_duotone"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. DUOTONE GRADIENT MAP")
                    duotone_input = gr.Image(label="Upload Image", type="numpy")
                    duotone_c1 = gr.ColorPicker(label="Shadow / Dark Tone", value="#FF4500") # Flame Orange
                    duotone_c2 = gr.ColorPicker(label="Highlight / Light Tone", value="#00F0FF") # Cyber Cyan
                    duotone_btn = gr.Button("🎨 MAP DUOTONE PALETTE", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. DUOTONE OUTPUT")
                    duotone_specs = gr.Textbox(label="Duotone Status", value="Ready", interactive=False)
                    duotone_output = gr.Image(label="Duotone Stylized Output", interactive=False)

    # Event Bindings
    comp_btn.click(
        fn=process_composite,
        inputs=[comp_input, comp_engine, comp_bg_style, comp_bg_color, comp_custom_bg, comp_shadow, colab_url_input],
        outputs=[comp_output, cutout_output, comp_specs, preview_subtabs]
    )
    
    upscale_btn.click(fn=process_upscale, inputs=[upscale_input, sharpness_slider, color_boost_slider], outputs=[upscale_output, upscale_specs])
    wm_btn.click(fn=process_watermark, inputs=[wm_base, wm_logo, wm_pos, wm_scale, wm_opacity, wm_rotation], outputs=[wm_output, wm_specs])
    fx_btn.click(fn=process_cyber_fx, inputs=[fx_input, fx_type, fx_intensity], outputs=[fx_output, fx_specs])
    aura_btn.click(fn=process_energy_aura, inputs=[aura_input, aura_color, aura_radius, aura_blur], outputs=[aura_output, aura_specs])
    canvas_btn.click(fn=process_canvas_resize, inputs=[canvas_input, canvas_ratio, canvas_bg_color, canvas_blur], outputs=[canvas_output, canvas_specs])
    glitch_btn.click(fn=process_glitch_effect, inputs=[glitch_input, glitch_shift, glitch_scanlines], outputs=[glitch_output, glitch_specs])
    lighting_btn.click(fn=process_cinematic_vignette, inputs=[lighting_input, vignette_slider, tint_slider], outputs=[lighting_output, lighting_specs])
    text_btn.click(fn=process_text_overlay, inputs=[text_input, text_header, text_sub, text_color, text_plate_op, text_pos], outputs=[text_output, text_specs])
    duotone_btn.click(fn=process_duotone_palette, inputs=[duotone_input, duotone_c1, duotone_c2], outputs=[duotone_output, duotone_specs])

    # Transfer Buttons
    send_upscale_btn.click(fn=lambda img: transfer_to_tab(img, "tab_upscale"), inputs=[comp_output], outputs=[upscale_input, main_tabs])
    send_aura_btn.click(fn=lambda img: transfer_to_tab(img, "tab_aura"), inputs=[cutout_output], outputs=[aura_input, main_tabs])
    send_watermark_btn.click(fn=lambda img: transfer_to_tab(img, "tab_watermark"), inputs=[comp_output], outputs=[wm_base, main_tabs])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.queue(default_concurrency_limit=8).launch(server_name="0.0.0.0", server_port=port)
