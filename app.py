"""
app.py - Main Gradio Launcher with Expanded Studio Features
"""
import sys
import traceback

print("--> Launching Shadow Flamez AI Studio Pro v5.5...", flush=True)

try:
    import os
    import time
    import io
    import zipfile
    from PIL import Image

    import config
    from utils import ImageUtils
    from diagnostics import diagnostics, logger
    from styles import STUDIO_CSS, STUDIO_HEADER_HTML, STUDIO_FOOTER_HTML
    from neural_engine import neural_engine
    from chroma_engine import ChromaKeyEngine
    from compositor import CompositingEngine

    import gradio as gr
except Exception as err:
    print(f"\n❌ STARTUP ERROR:\n{err}", flush=True)
    traceback.print_exc()
    sys.exit(1)


def format_status(msg: str, status_type: str = "info") -> str:
    color_map = {"info": "#00ffff", "success": "#00ff66", "warning": "#ffaa00", "error": "#ff0055"}
    col = color_map.get(status_type, "#00ffff")
    return f'<div class="status-badge" style="border-left-color: {col};">STATUS: {msg}</div>'


# Handlers
def process_studio_master(input_img, mode, ai_model, bg_opt, solid_col, aura_on, aura_col, aura_rad, shadow_on, shadow_x, shadow_y, shadow_blur, shadow_col):
    if input_img is None:
        return None, format_status("Please upload an image.", "warning")

    start = time.time()
    try:
        proc_img = ImageUtils.resize_for_performance(input_img, max_dim=2048)

        if mode == "AI Neural Removal":
            fg = neural_engine.remove_background(proc_img, model_name=ai_model)
        else:
            fg = ChromaKeyEngine.process_keying(proc_img, screen_type=mode)

        if shadow_on:
            fg = neural_engine.apply_drop_shadow(fg, offset_x=int(shadow_x), offset_y=int(shadow_y), blur_r=int(shadow_blur), shadow_hex=shadow_col)

        if aura_on:
            fg = neural_engine.generate_neon_aura(fg, aura_color_hex=aura_col, blur_radius=int(aura_rad))

        final_out = CompositingEngine.composite_layers(fg, bg_option=bg_opt, solid_hex=solid_col)
        elapsed = round(time.time() - start, 2)
        diagnostics.record_task("Studio Master Render", elapsed)
        return final_out, format_status(f"Rendered in {elapsed}s", "success")
    except Exception as e:
        return None, format_status(f"Error: {str(e)}", "error")


def process_cyber_suite(input_img, upscale_on, sharpness, outline_on, outline_col, stroke_w, glitch_on, glitch_offset, lut_preset, pixel_on, pixel_size):
    if input_img is None:
        return None, format_status("Upload an image for Cyber Suite.", "warning")

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
        return res, format_status(f"Cyber Suite applied in {elapsed}s", "success")
    except Exception as e:
        return None, format_status(f"FX Error: {str(e)}", "error")


def build_studio():
    with gr.Blocks(title="Shadow Flamez AI Studio Pro v5.5", css=STUDIO_CSS) as app:
        gr.HTML(STUDIO_HEADER_HTML)

        with gr.Tabs():
            # TAB 1: AI STUDIO MASTER
            with gr.Tab("🔥 AI Background & Lighting Studio"):
                with gr.Row():
                    with gr.Column(scale=1):
                        in_img = gr.Image(type="pil", label="Source Image")
                        mode = gr.Radio(["AI Neural Removal", "Green Screen Keying", "Blue Screen Keying"], value="AI Neural Removal", label="Extraction Engine")
                        ai_model = gr.Dropdown(["u2net", "isnet-general-use", "u2netp", "silueta"], value="u2net", label="AI Model")
                        bg_opt = gr.Radio(["Transparent (PNG)", "Checkerboard Preview", "Solid Custom Color"], value="Transparent (PNG)", label="Background Mode")
                        solid_col = gr.ColorPicker(value="#0B0E14", label="Background Color")
                        
                        gr.Markdown("#### 🌑 Dynamic Drop Shadow FX")
                        shadow_on = gr.Checkbox(label="Enable Realistic Drop Shadow", value=False)
                        shadow_x = gr.Slider(-50, 50, value=15, label="Offset X")
                        shadow_y = gr.Slider(-50, 50, value=20, label="Offset Y")
                        shadow_blur = gr.Slider(0, 40, value=15, label="Shadow Blur Radius")
                        shadow_col = gr.ColorPicker(value="#000000", label="Shadow Color")

                        gr.Markdown("#### ✨ Neon Halo Backglow")
                        aura_on = gr.Checkbox(label="Enable Neon Aura Glow", value=False)
                        aura_col = gr.ColorPicker(value="#00FFFF", label="Aura Glow Color")
                        aura_rad = gr.Slider(5, 50, value=20, label="Glow Radius")
                        
                        btn_exec = gr.Button("🔥 RENDER MASTER OUTPUT", elem_classes=["cyber-button"])

                    with gr.Column(scale=1):
                        status_box = gr.HTML(format_status("System Ready.", "info"))
                        out_img = gr.Image(type="pil", label="Render Result", format="png")

                btn_exec.click(
                    process_studio_master,
                    inputs=[in_img, mode, ai_model, bg_opt, solid_col, aura_on, aura_col, aura_rad, shadow_on, shadow_x, shadow_y, shadow_blur, shadow_col],
                    outputs=[out_img, status_box]
                )

            # TAB 2: CYBER & COLOR SUITE
            with gr.Tab("⚡ Cyber Graphics & Color Grade"):
                with gr.Row():
                    with gr.Column(scale=1):
                        cyber_in = gr.Image(type="pil", label="Input Image")
                        
                        gr.Markdown("#### 🎨 Cinematic LUT Color Grading")
                        lut_preset = gr.Dropdown(["None", "Cyberpunk Neo", "Matrix Green", "Golden Hour", "Noir Monochrome"], value="None", label="Color Grade Preset")
                        
                        gr.Markdown("#### 👾 RGB Glitch & Pixel Art")
                        glitch_on = gr.Checkbox(label="Enable RGB Glitch Split", value=False)
                        glitch_offset = gr.Slider(1, 30, value=10, label="Glitch Displacement")
                        pixel_on = gr.Checkbox(label="Enable 8-Bit Pixel Art Effect", value=False)
                        pixel_size = gr.Slider(2, 32, value=12, label="Pixel Density")

                        gr.Markdown("#### ⚡ Cyber Outline & Upscaler")
                        outline_on = gr.Checkbox(label="Enable Cyber Outline Contouring", value=False)
                        outline_col = gr.ColorPicker(value="#FF007F", label="Outline Color")
                        stroke_w = gr.Slider(1, 15, value=4, label="Stroke Width")
                        upscale_on = gr.Checkbox(label="Enable AI 4X Super Resolution Scaler", value=True)
                        sharp = gr.Slider(1.0, 3.0, value=1.5, step=0.1, label="Sharpening")

                        btn_cyber = gr.Button("⚡ APPLY CYBER SUITE", elem_classes=["cyber-button"])

                    with gr.Column(scale=1):
                        cyber_status = gr.HTML(format_status("Cyber Suite Ready.", "info"))
                        cyber_out = gr.Image(type="pil", label="Enhanced Output", format="png")

                btn_cyber.click(
                    process_cyber_suite,
                    inputs=[cyber_in, upscale_on, sharp, outline_on, outline_col, stroke_w, glitch_on, glitch_offset, lut_preset, pixel_on, pixel_size],
                    outputs=[cyber_out, cyber_status]
                )

            # TAB 3: DIAGNOSTICS
            with gr.Tab("📊 Live Diagnostics"):
                diag_html = gr.HTML(diagnostics.generate_report_html())
                btn_ref = gr.Button("🔄 REFRESH METRICS")
                btn_ref.click(lambda: diagnostics.generate_report_html(), outputs=[diag_html])

        gr.HTML(STUDIO_FOOTER_HTML)
    return app


if __name__ == "__main__":
    demo_app = build_studio()
    demo_app.queue().launch(server_name="0.0.0.0", server_port=config.PORT, share=False)
