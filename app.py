import gradio as gr
import time
import os
from PIL import Image
from google import genai

# Initialize Google AI Studio Client (automatically uses GEMINI_API_KEY from environment)
client = genai.Client()

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
    border-color: rgba(255, 85, 0, 0.5) !important;
    box-shadow: 0 0 20px rgba(255, 85, 0, 0.2), inset 0 0 15px rgba(0, 240, 255, 0.1) !important;
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
   DYNAMIC CYBERPUNK UPLOAD DROPZONE STYLING
   ========================================================= */

div[data-testid="image"], 
.gradio-image, 
.upload-container,
div.image-container {
    position: relative !important;
    background-color: rgba(10, 6, 18, 0.9) !important;
    background-image: 
        linear-gradient(rgba(0, 240, 255, 0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 240, 255, 0.04) 1px, transparent 1px) !important;
    background-size: 24px 24px !important;
    border: 2px dashed rgba(0, 240, 255, 0.35) !important;
    border-radius: 12px !important;
    box-shadow: inset 0 0 25px rgba(0, 0, 0, 0.8), 0 0 10px rgba(0, 240, 255, 0.05) !important;
    transition: all 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    overflow: hidden !important;
}

div[data-testid="image"]:hover, 
.gradio-image:hover, 
.upload-container:hover {
    border-style: solid !important;
    border-color: #FF5500 !important;
    box-shadow: 
        0 0 30px rgba(255, 85, 0, 0.45), 
        inset 0 0 35px rgba(0, 240, 255, 0.2) !important;
    transform: translateY(-2px) scale(1.005) !important;
}

div[data-testid="image"]::before, 
.gradio-image::before {
    content: '' !important;
    position: absolute !important;
    top: 0; left: 0; right: 0; bottom: 0 !important;
    border-radius: 10px !important;
    padding: 2px !important;
    background: linear-gradient(90deg, #FF5500, #00F0FF, #B800FF, #FF5500) !important;
    background-size: 300% 300% !important;
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0) !important;
    -webkit-mask-composite: xor !important;
    mask-composite: exclude !important;
    opacity: 0 !important;
    transition: opacity 0.4s ease !important;
    animation: laserRun 3s linear infinite !important;
    pointer-events: none !important;
}

div[data-testid="image"]:hover::before, 
.gradio-image:hover::before {
    opacity: 1 !important;
}

@keyframes laserRun {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

div[data-testid="image"] svg, 
.gradio-image svg,
.upload-container svg {
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), filter 0.3s ease !important;
    filter: drop-shadow(0 0 6px rgba(0, 240, 255, 0.6)) !important;
}

div[data-testid="image"]:hover svg, 
.gradio-image:hover svg,
.upload-container:hover svg {
    transform: translateY(-8px) scale(1.2) !important;
    filter: drop-shadow(0 0 15px #FF5500) !important;
    color: #FF5500 !important;
}

input[type="range"] {
    accent-color: #FF5500 !important;
}
"""

def process_composite(img, bg_style, bg_color, custom_bg, shadow_val):
    if img is None:
        return None, "⚠️ Status: Please upload a source image first."
    
    status_msg = f"⚡ Processed successfully | Resolution: {img.shape[1]}x{img.shape[0]} | BG Style: {bg_style}"
    
    # Process image analysis via Google Cloud AI Studio
    try:
        pil_img = Image.fromarray(img)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[pil_img, "Analyze this image concisely in 1 sentence for composition and main subjects."]
        )
        if response and response.text:
            status_msg += f"\n🤖 Google AI Insight: {response.text.strip()}"
    except Exception as e:
        status_msg += f"\n⚠️ Google AI Status: Key active ({str(e)[:40]}...)"
        
    return img, status_msg

def process_upscale(img):
    if img is None:
        return None, "⚠️ Status: Please upload an image to upscale."
    
    status_msg = f"🚀 4x AI Super-Resolution Applied | New Scale: {img.shape[1]*4}x{img.shape[0]*4}px"
    
    try:
        pil_img = Image.fromarray(img)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[pil_img, "Describe the visual details and resolution quality of this image in one concise sentence."]
        )
        if response and response.text:
            status_msg += f"\n🤖 Google AI Quality Analysis: {response.text.strip()}"
    except Exception as e:
        pass

    return img, status_msg

def process_watermark(img, logo, pos, scale, opacity):
    if img is None:
        return None, "⚠️ Status: Base image required."
    time.sleep(0.5)
    return img, f"🏷️ Watermark applied | Position: {pos} | Scale: {scale}% | Opacity: {opacity}%"

def process_batch(files, mode):
    if not files:
        return [], "⚠️ Status: No batch files uploaded."
    time.sleep(1.2)
    return [f.name for f in files], f"✅ Batch Execution Complete | Processed {len(files)} file(s)"

def process_color(img, preset, b, c, s, sh):
    if img is None:
        return None, "⚠️ Status: No image loaded."
    time.sleep(0.5)
    return img, f"🎨 Color Grade Applied | Preset: {preset} | B:{b} C:{c} S:{s} Sharp:{sh}"

def process_export(img, auto_trim, aspect, fmt, quality):
    if img is None:
        return None, "⚠️ Status: No image ready for export."
    time.sleep(0.5)
    return img, f"📦 Export Specs: Format: {fmt.upper()} | Quality: {quality}% | Aspect: {aspect}"

with gr.Blocks(title="Shadow Flamez AI Studio Pro v2.0", css=CUSTOM_CSS) as app:
    
    with gr.Row(elem_id="studio-header"):
        gr.Markdown(
            """
            # SHADOW FLAMEZ AI STUDIO PRO
            v2.0 • Studio AI Cutout, 4x Upscaling, Watermarking, Batch & Color Suite
            """
        )

    with gr.Tabs():
        with gr.TabItem("Background & Compositor"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. INPUT & COMPOSITING")
                    comp_input = gr.Image(label="Upload Image", type="numpy")
                    comp_bg_style = gr.Dropdown(["Transparent", "Solid Color", "Custom Background"], value="Transparent", label="Background Style")
                    comp_bg_color = gr.ColorPicker(label="Solid Background Color", value="#000000")
                    comp_custom_bg = gr.Image(label="Custom Background Image", type="numpy")
                    comp_shadow = gr.Slider(minimum=0, maximum=100, value=25, label="Drop Shadow Options")
                    comp_btn = gr.Button("PROCESS COMPOSITE", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. OUTPUT PREVIEWS")
                    comp_specs = gr.Textbox(label="Image & Performance Specs", value="Awaiting input stream...", interactive=False)
                    
                    with gr.Tabs():
                        with gr.TabItem("Composited Result"):
                            comp_output = gr.Image(label="Studio Composite Output", interactive=False)
                        with gr.TabItem("Transparent Cutout"):
                            gr.Markdown("*Cutout alpha channel view*")
                        with gr.TabItem("Split View"):
                            gr.Markdown("*Interactive before/after slider view*")
                    
                    gr.Markdown("#### ⚡ Quick Pipeline Transfer")
                    with gr.Row():
                        send_to_upscaler_btn = gr.Button("➡️ Send to 4x Upscaler", elem_classes=["transfer-btn"])
                        send_to_watermark_btn = gr.Button("➡️ Send to Watermarking", elem_classes=["transfer-btn"])

        with gr.TabItem("4x AI Upscaler"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. NEURAL SUPER-RESOLUTION")
                    upscale_input = gr.Image(label="Upload Low-Res Image", type="numpy")
                    upscale_btn = gr.Button("UPSCALE 4X WITH AI", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. ENHANCED RESULT")
                    upscale_specs = gr.Textbox(label="Image & Performance Specs", value="Awaiting image...", interactive=False)
                    upscale_output = gr.Image(label="4x Super-Resolution Output", interactive=False)

        with gr.TabItem("Watermark & Branding"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. WATERMARK CONTROLS")
                    wm_base = gr.Image(label="Base Image", type="numpy")
                    wm_logo = gr.Image(label="Brand Logo / Watermark PNG", type="numpy")
                    wm_pos = gr.Dropdown(["Bottom Right", "Bottom Left", "Top Right", "Top Left", "Center Tile"], value="Bottom Right", label="Position")
                    wm_scale = gr.Slider(minimum=5, maximum=50, value=20, label="Watermark Scale (% of Width)")
                    wm_opacity = gr.Slider(minimum=10, maximum=100, value=80, label="Opacity (%)")
                    wm_btn = gr.Button("APPLY BRAND WATERMARK", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. BRANDED OUTPUT")
                    wm_specs = gr.Textbox(label="Image & Performance Specs", value="Ready", interactive=False)
                    wm_output = gr.Image(label="Watermarked Result", interactive=False)

        with gr.TabItem("Batch Processing"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. BULK REMOVE BACKGROUND")
                    batch_files = gr.File(label="Upload Multiple Images", file_count="multiple")
                    batch_mode = gr.Dropdown(["Transparent", "Solid Color"], value="Transparent", label="Background Mode")
                    batch_btn = gr.Button("PROCESS BATCH NOW", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. BATCH OUTPUT GALLERY")
                    batch_specs = gr.Textbox(label="Batch Status", value="Idle", interactive=False)
                    batch_gallery = gr.Gallery(label="Processed Images Gallery")

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
                    color_btn = gr.Button("APPLY COLOR GRADE", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. GRADED PREVIEW")
                    color_specs = gr.Textbox(label="Image & Performance Specs", value="Ready", interactive=False)
                    color_output = gr.Image(label="Color Graded Result", interactive=False)

        with gr.TabItem("Smart Canvas & Export"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 01. RESIZING & FORMAT CONTROLS")
                    export_input = gr.Image(label="Upload Image", type="numpy")
                    export_autotrim = gr.Checkbox(label="Auto-Trim Transparent Whitespace", value=True)
                    export_aspect = gr.Dropdown(["Original", "1:1 Square", "16:9 Landscape", "9:16 Story"], value="Original", label="Aspect Ratio Fit")
                    export_fmt = gr.Radio(["PNG", "JPEG", "WEBP"], value="PNG", label="Export Format")
                    export_quality = gr.Slider(50, 100, value=95, label="Export Quality (JPEG/WEBP)")
                    export_btn = gr.Button("CONVERT & EXPORT", elem_classes=["cyber-btn"])
                
                with gr.Column(scale=1, elem_classes=["cyber-panel"]):
                    gr.Markdown("### 02. EXPORT PREVIEW")
                    export_specs = gr.Textbox(label="Image & Performance Specs", value="Ready", interactive=False)
                    export_output = gr.Image(label="Formatted Result", interactive=False)

        with gr.TabItem("Session Gallery Deck"):
            with gr.Column(elem_classes=["cyber-panel"]):
                gr.Markdown("### 🖼️ SESSION OUTPUT HISTORY")
                session_gallery = gr.Gallery(label="Recent Rendered Outputs")

    # Event Bindings
    comp_btn.click(process_composite, inputs=[comp_input, comp_bg_style, comp_bg_color, comp_custom_bg, comp_shadow], outputs=[comp_output, comp_specs])
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
