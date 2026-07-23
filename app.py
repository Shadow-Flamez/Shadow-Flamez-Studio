import os
import io
import gc
import zipfile

# ======================================================
# 1. FORCE CPU-ONLY MODE (Disables ONNX GPU discovery delay)
# ======================================================
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["ORT_DISABLE_TELEMETRY"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import gradio as gr

# Global cache for AI model sessions
REMBG_SESSIONS = {}

def get_rembg_session(model_name: str = "u2netp"):
    """
    Retrieves or initializes a rembg session on demand.
    Defers ONNX initialization until a user actually clicks 'Remove Background'.
    """
    if model_name not in REMBG_SESSIONS:
        import onnxruntime as ort
        from rembg import new_session

        # Mute ONNX warnings/logs
        ort.set_default_logger_severity(3)

        # Restrict CPU threads for Render's free tier
        ort_options = ort.SessionOptions()
        ort_options.intra_op_num_threads = 1
        ort_options.inter_op_num_threads = 1

        REMBG_SESSIONS[model_name] = new_session(
            model_name, 
            providers=["CPUExecutionProvider"], 
            sess_options=ort_options
        )
    return REMBG_SESSIONS[model_name]


# ======================================================
# 2. CORE OPTIMIZED AI & IMAGE PROCESSING ENGINE
# ======================================================

def smart_bg_removal(
    img: Image.Image,
    model_name: str = "u2netp",
    alpha_matting: bool = False,
    af_fg_thresh: int = 240,
    af_bg_thresh: int = 10,
    af_erode_size: int = 10,
    max_proc_dim: int = 1024
):
    if img is None:
        return None, None

    from rembg import remove

    orig_w, orig_h = img.size

    # Scale down for neural network processing if image is large
    if max(orig_w, orig_h) > max_proc_dim:
        scale = max_proc_dim / float(max(orig_w, orig_h))
        work_w, work_h = int(orig_w * scale), int(orig_h * scale)
        work_img = img.resize((work_w, work_h), Image.Resampling.LANCZOS)
    else:
        work_img = img.copy()

    # Get session & extract alpha mask
    session = get_rembg_session(model_name)
    mask_png = remove(
        work_img,
        session=session,
        only_mask=True,
        alpha_matting=alpha_matting,
        alpha_matting_foreground_threshold=af_fg_thresh,
        alpha_matting_background_threshold=af_bg_thresh,
        alpha_matting_erode_size=af_erode_size
    )

    # Upscale mask back to original resolution
    full_mask = mask_png.resize((orig_w, orig_h), Image.Resampling.BICUBIC)

    # Apply mask to full-resolution input image
    result = img.convert("RGBA")
    result.putalpha(full_mask)

    del work_img, mask_png
    gc.collect()

    return result, full_mask

# ======================================================
# 3. TAB 1: BACKGROUND REMOVER & ALPHA MATTING STUDIO
# ======================================================

def process_tab1_bg_removal(
    input_img,
    model_name,
    alpha_matting,
    fg_thresh,
    bg_thresh,
    erode_size,
    invert_mask,
    bg_color_hex,
    feather_radius
):
    if input_img is None:
        return None, None, "Please upload an image first."

    # Execute smart BG removal
    result_rgba, alpha_mask = smart_bg_removal(
        input_img,
        model_name=model_name,
        alpha_matting=alpha_matting,
        af_fg_thresh=fg_thresh,
        af_bg_thresh=bg_thresh,
        af_erode_size=erode_size
    )

    if invert_mask:
        inv_alpha = ImageOps.invert(alpha_mask)
        result_rgba = input_img.convert("RGBA")
        result_rgba.putalpha(inv_alpha)
        alpha_mask = inv_alpha

    if feather_radius > 0:
        alpha_mask = alpha_mask.filter(ImageFilter.GaussianBlur(feather_radius))
        result_rgba.putalpha(alpha_mask)

    # Optional background fill
    final_output = result_rgba
    if bg_color_hex and bg_color_hex != "Transparent":
        bg = Image.new("RGBA", result_rgba.size, bg_color_hex)
        final_output = Image.alpha_composite(bg, result_rgba).convert("RGB")

    info = f"Processed successfully at original resolution ({input_img.width}x{input_img.height} px)."
    
    del alpha_mask
    gc.collect()
    
    return final_output, result_rgba, info


# ======================================================
# 4. TAB 2: ADVANCED BACKGROUND COMPOSITOR
# ======================================================

def process_tab2_composite(
    fg_img,
    bg_img,
    model_name,
    scale_factor,
    offset_x,
    offset_y,
    rotation_deg,
    bg_blur,
    shadow_opacity,
    shadow_blur,
    shadow_dx,
    shadow_dy,
    match_brightness
):
    if fg_img is None or bg_img is None:
        return None, "Both foreground and background images are required."

    # Extract cutout
    fg_cutout, mask = smart_bg_removal(fg_img, model_name=model_name)

    # Resize background to match foreground resolution base
    bg_w, bg_h = bg_img.size
    fg_w, fg_h = fg_cutout.size

    base_bg = bg_img.convert("RGBA")
    if bg_blur > 0:
        base_bg = base_bg.filter(ImageFilter.GaussianBlur(bg_blur))

    # Match brightness if requested
    if match_brightness:
        bg_np = np.array(bg_img.convert("L"))
        fg_np = np.array(fg_img.convert("L"))
        bg_mean = np.mean(bg_np) / 255.0
        fg_mean = np.mean(fg_np) / 255.0
        if fg_mean > 0:
            ratio = bg_mean / fg_mean
            enhancer = ImageEnhance.Brightness(fg_cutout)
            fg_cutout = enhancer.enhance(max(0.5, min(1.5, ratio)))

    # Apply scaling and rotation to foreground cutout
    if scale_factor != 1.0 or rotation_deg != 0:
        new_w = max(1, int(fg_w * scale_factor))
        new_h = max(1, int(fg_h * scale_factor))
        fg_cutout = fg_cutout.resize((new_w, new_h), Image.Resampling.LANCZOS)
        if rotation_deg != 0:
            fg_cutout = fg_cutout.rotate(rotation_deg, expand=True, resample=Image.Resampling.BICUBIC)

    # Canvas creation
    canvas = Image.new("RGBA", base_bg.size, (0, 0, 0, 0))

    # Compute placement position
    place_x = (base_bg.width - fg_cutout.width) // 2 + offset_x
    place_y = (base_bg.height - fg_cutout.height) // 2 + offset_y

    # Render drop shadow if requested
    if shadow_opacity > 0:
        shadow_mask = fg_cutout.split()[3]
        shadow = Image.new("RGBA", fg_cutout.size, (0, 0, 0, int(255 * shadow_opacity)))
        shadow.putalpha(shadow_mask)
        if shadow_blur > 0:
            shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
        
        canvas.paste(shadow, (place_x + shadow_dx, place_y + shadow_dy), shadow)

    # Paste subject
    canvas.paste(fg_cutout, (place_x, place_y), fg_cutout)

    # Composite onto background
    final_comp = Image.alpha_composite(base_bg, canvas).convert("RGB")

    del base_bg, canvas, fg_cutout
    gc.collect()

    return final_comp, "Composition rendered successfully."


# ======================================================
# 5. TAB 3: EDGE MATTING, RETOUCHING & DEFRINGING
# ======================================================

def process_tab3_retouch(
    input_img,
    erode_dilate_size,
    edge_blur,
    defringe_strength,
    contrast_mask
):
    if input_img is None:
        return None, "Upload an image with transparency (RGBA) or run BG removal first."

    if input_img.mode != "RGBA":
        input_img, _ = smart_bg_removal(input_img)

    r, g, b, alpha = input_img.split()
    alpha_np = np.array(alpha)

    # Morphological Erode/Dilate on Alpha channel
    if erode_dilate_size != 0:
        kernel_size = abs(erode_dilate_size) * 2 + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        if erode_dilate_size < 0:
            alpha_np = cv2.erode(alpha_np, kernel, iterations=1)
        else:
            alpha_np = cv2.dilate(alpha_np, kernel, iterations=1)

    # Defringing (color decontamination on fringe edges)
    rgb_np = np.array(input_img.convert("RGB"))
    if defringe_strength > 0:
        alpha_normalized = alpha_np.astype(float) / 255.0
        edge_region = (alpha_normalized > 0.05) & (alpha_normalized < 0.95)
        
        # Apply median blur to boundary pixels
        blurred_rgb = cv2.medianBlur(rgb_np, 5)
        blend_factor = (defringe_strength / 100.0)
        for c in range(3):
            rgb_np[:, :, c] = np.where(edge_region, 
                                       (1 - blend_factor) * rgb_np[:, :, c] + blend_factor * blurred_rgb[:, :, c], 
                                       rgb_np[:, :, c])

    # Reconstruct Image
    mod_alpha = Image.fromarray(alpha_np)
    if edge_blur > 0:
        mod_alpha = mod_alpha.filter(ImageFilter.GaussianBlur(edge_blur))

    if contrast_mask > 1.0:
        enhancer = ImageEnhance.Contrast(mod_alpha)
        mod_alpha = enhancer.enhance(contrast_mask)

    result = Image.fromarray(rgb_np).convert("RGBA")
    result.putalpha(mod_alpha)

    del alpha_np, rgb_np
    gc.collect()

    return result, "Edge retouching and defringing complete."


# ======================================================
# 6. TAB 4: PROFESSIONAL ENHANCER & PRESET STUDIO
# ======================================================

def apply_image_preset(img: Image.Image, preset_name: str) -> Image.Image:
    """Applies high-speed OpenCV filter presets."""
    img_np = np.array(img.convert("RGB"))

    if preset_name == "Vintage Warm":
        img_np = cv2.transform(img_np, np.array([
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131]
        ]))
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)

    elif preset_name == "Cyberpunk Glow":
        img_np[:, :, 0] = np.clip(img_np[:, :, 0] * 1.2, 0, 255)
        img_np[:, :, 2] = np.clip(img_np[:, :, 2] * 1.3, 0, 255)

    elif preset_name == "Cinematic Cool":
        img_np[:, :, 0] = np.clip(img_np[:, :, 0] * 0.85, 0, 255)
        img_np[:, :, 2] = np.clip(img_np[:, :, 2] * 1.25, 0, 255)

    elif preset_name == "High Contrast B&W":
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        gray = cv2.equalizeHist(gray)
        img_np = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

    elif preset_name == "Portrait Soft":
        img_np = cv2.bilateralFilter(img_np, 9, 75, 75)

    return Image.fromarray(img_np)


def process_tab4_enhancer(
    input_img,
    preset,
    brightness,
    contrast,
    saturation,
    sharpness,
    temperature,
    vignette_strength
):
    if input_img is None:
        return None, "Upload an image to adjust enhancements."

    work_img = input_img.copy()

    # Apply preset filter
    if preset != "None":
        work_img = apply_image_preset(work_img, preset)

    # Basic adjustments
    if brightness != 1.0:
        work_img = ImageEnhance.Brightness(work_img).enhance(brightness)
    if contrast != 1.0:
        work_img = ImageEnhance.Contrast(work_img).enhance(contrast)
    if saturation != 1.0:
        work_img = ImageEnhance.Color(work_img).enhance(saturation)
    if sharpness != 1.0:
        work_img = ImageEnhance.Sharpness(work_img).enhance(sharpness)

    # Temperature adjustment
    if temperature != 0:
        img_np = np.array(work_img.convert("RGB")).astype(float)
        if temperature > 0: # Warm
            img_np[:, :, 0] += temperature * 15
            img_np[:, :, 2] -= temperature * 10
        else: # Cool
            img_np[:, :, 0] += temperature * 10
            img_np[:, :, 2] -= temperature * 15
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)
        work_img = Image.fromarray(img_np)

    # Vignette effect
    if vignette_strength > 0:
        w, h = work_img.size
        kernel_x = cv2.getGaussianKernel(w, w / 2)
        kernel_y = cv2.getGaussianKernel(h, h / 2)
        kernel = kernel_y * kernel_x.T
        mask = kernel / kernel.max()
        
        vignette_mask = 1 - (1 - mask) * vignette_strength
        vignette_mask = np.dstack([vignette_mask] * 3)

        img_np = (np.array(work_img.convert("RGB")) * vignette_mask).astype(np.uint8)
        work_img = Image.fromarray(img_np)

    gc.collect()
    return work_img, "Enhancements applied."


# ======================================================
# 7. TAB 5: SMART RESIZER, CROP & SOCIAL TEMPLATES
# ======================================================

SOCIAL_TEMPLATES = {
    "Custom": None,
    "Instagram Post (1080x1080)": (1080, 1080),
    "Instagram Story/Reel (1080x1920)": (1080, 1920),
    "YouTube Thumbnail (1280x720)": (1280, 720),
    "Twitter / X Header (1500x500)": (1500, 500),
    "LinkedIn Banner (1584x396)": (1584, 396),
    "Passport Photo (600x600)": (600, 600)
}

def update_resizer_dimensions(template_name):
    if template_name in SOCIAL_TEMPLATES and SOCIAL_TEMPLATES[template_name] is not None:
        w, h = SOCIAL_TEMPLATES[template_name]
        return w, h
    return gr.update(), gr.update()


def process_tab5_resizer(
    input_img,
    template,
    target_width,
    target_height,
    crop_mode,
    output_format,
    quality_setting
):
    if input_img is None:
        return None, None, "Upload an image to resize."

    w = int(target_width)
    h = int(target_height)

    if crop_mode == "Fit / Pad":
        res_img = ImageOps.pad(input_img, (w, h), color=(255, 255, 255))
    elif crop_mode == "Center Crop":
        res_img = ImageOps.fit(input_img, (w, h), centering=(0.5, 0.5))
    else: # Stretch
        res_img = input_img.resize((w, h), Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    save_fmt = output_format.upper()
    if save_fmt == "JPG":
        save_fmt = "JPEG"
        res_img = res_img.convert("RGB")

    res_img.save(buffer, format=save_fmt, quality=quality_setting)
    buffer.seek(0)

    file_size_kb = len(buffer.getvalue()) / 1024.0
    status_msg = f"Resized to {w}x{h} px | Format: {output_format} | Size: ~{file_size_kb:.1f} KB"

    out_file_path = f"resized_output.{output_format.lower()}"
    res_img.save(out_file_path, format=save_fmt, quality=quality_setting)

    gc.collect()
    return res_img, out_file_path, status_msg


# ======================================================
# 8. TAB 6: BATCH PROCESSOR
# ======================================================

def process_tab6_batch(file_list, model_name, apply_preset_name):
    if not file_list:
        return None, "No files uploaded for batch processing."

    zip_buffer = io.BytesIO()
    processed_count = 0

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, file_obj in enumerate(file_list):
            try:
                img = Image.open(file_obj.name)
                
                # Apply background removal
                out_img, _ = smart_bg_removal(img, model_name=model_name)

                # Optional preset
                if apply_preset_name != "None":
                    out_img = apply_image_preset(out_img, apply_preset_name)

                img_byte_arr = io.BytesIO()
                out_img.save(img_byte_arr, format="PNG")
                
                filename = f"processed_{idx+1}_" + os.path.basename(file_obj.name)
                filename = os.path.splitext(filename)[0] + ".png"
                
                zip_file.writestr(filename, img_byte_arr.getvalue())
                processed_count += 1
                
                del img, out_img, img_byte_arr
                gc.collect()

            except Exception as e:
                print(f"Error processing file {file_obj.name}: {e}")

    zip_buffer.seek(0)
    zip_path = "batch_processed_images.zip"
    with open(zip_path, "wb") as f:
        f.write(zip_buffer.getvalue())

    return zip_path, f"Successfully processed {processed_count} images into ZIP."


# ======================================================
# 9. TAB 7: IMAGE INSPECTOR & PALETTE EXTRACTOR
# ======================================================

def process_tab7_inspector(input_img):
    if input_img is None:
        return "No image provided.", None

    w, h = input_img.size
    aspect_ratio = round(w / float(h), 2)
    mode = input_img.mode
    
    img_np = np.array(input_img.convert("RGB"))
    mean_color = np.mean(img_np, axis=(0, 1)).astype(int)
    brightness = int(np.mean(mean_color))

    # K-Means dominant color palette extraction
    pixels = img_np.reshape(-1, 3).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixels[::10], 5, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    colors = centers.astype(int)
    
    palette_height = 100
    palette_width = 500
    palette_img = np.zeros((palette_height, palette_width, 3), dtype=np.uint8)
    
    swatch_w = palette_width // 5
    hex_codes = []
    for i, c in enumerate(colors):
        palette_img[:, i*swatch_w:(i+1)*swatch_w] = c
        hex_code = f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"
        hex_codes.append(hex_code)

    report = f"""
    ### 📊 Image Metadata Report
    * **Dimensions:** {w} x {h} pixels
    * **Aspect Ratio:** {aspect_ratio}:1
    * **Color Mode:** {mode}
    * **Average Brightness:** {brightness} / 255
    * **Dominant Color Palette (Hex):** {', '.join(hex_codes)}
    """

    return report, Image.fromarray(palette_img)


# ======================================================
# 10. FULL GRADIO BLOCKS USER INTERFACE CONSTRUCTION
# ======================================================

def build_app():
    custom_theme = gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="slate",
    )

    with gr.Blocks(theme=custom_theme, title="Studio AI Suite Pro") as demo:
        gr.Markdown(
            """
            # 🎨 Studio AI Image Suite Pro
            **Complete Cloud-Optimized Neural & Computer Vision Image Suite**
            """
        )

        with gr.Tabs():

            # --------------------------------------------------
            # TAB 1: BACKGROUND REMOVER
            # --------------------------------------------------
            with gr.TabItem("🖼️ Background Remover"):
                gr.Markdown("### AI Background Removal & Alpha Matting")
                with gr.Row():
                    with gr.Column():
                        t1_input = gr.Image(type="pil", label="Source Image")
                        t1_model = gr.Dropdown(
                            ["u2netp", "u2net", "isnet-general-use", "silueta"],
                            value="u2netp",
                            label="Model (u2netp is fastest & lowest memory)"
                        )
                        
                        with gr.Accordion("Advanced Alpha Matting Settings", open=False):
                            t1_matting = gr.Checkbox(label="Enable Alpha Matting", value=False)
                            t1_fg_thresh = gr.Slider(0, 255, value=240, step=5, label="Foreground Threshold")
                            t1_bg_thresh = gr.Slider(0, 255, value=10, step=5, label="Background Threshold")
                            t1_erode = gr.Slider(0, 50, value=10, step=1, label="Erode Size")

                        with gr.Accordion("Refinement & Fill", open=False):
                            t1_invert = gr.Checkbox(label="Invert Alpha Mask", value=False)
                            t1_feather = gr.Slider(0, 20, value=0, step=1, label="Feather Edges")
                            t1_bg_color = gr.Dropdown(
                                ["Transparent", "#FFFFFF", "#000000", "#FF0000", "#00FF00", "#00FF00"],
                                value="Transparent",
                                label="Background Fill Color"
                            )

                        t1_btn = gr.Button("Remove Background", variant="primary")

                    with gr.Column():
                        t1_output_main = gr.Image(type="pil", label="Final Output", format="png")
                        t1_output_rgba = gr.Image(type="pil", label="Transparent Cutout (RGBA)", format="png")
                        t1_status = gr.Textbox(label="Status / Metadata", interactive=False)

                t1_btn.click(
                    fn=process_tab1_bg_removal,
                    inputs=[t1_input, t1_model, t1_matting, t1_fg_thresh, t1_bg_thresh, t1_erode, t1_invert, t1_bg_color, t1_feather],
                    outputs=[t1_output_main, t1_output_rgba, t1_status]
                )

            # --------------------------------------------------
            # TAB 2: BACKGROUND COMPOSITOR
            # --------------------------------------------------
            with gr.TabItem("🌄 Background Compositor"):
                gr.Markdown("### Composite Subject onto New Backdrop with Drop Shadows & Lighting")
                with gr.Row():
                    with gr.Column():
                        t2_fg = gr.Image(type="pil", label="Foreground Subject")
                        t2_bg = gr.Image(type="pil", label="New Background")
                        t2_model = gr.Dropdown(["u2netp", "u2net"], value="u2netp", label="Extraction Model")

                        with gr.Accordion("Position & Scale", open=True):
                            t2_scale = gr.Slider(0.1, 2.0, value=1.0, step=0.05, label="Scale Subject")
                            t2_offx = gr.Slider(-500, 500, value=0, step=10, label="Offset X")
                            t2_offy = gr.Slider(-500, 500, value=0, step=10, label="Offset Y")
                            t2_rot = gr.Slider(-180, 180, value=0, step=5, label="Rotate Deg")

                        with gr.Accordion("Shadow & Lighting", open=False):
                            t2_bg_blur = gr.Slider(0, 30, value=0, step=1, label="Background Blur")
                            t2_sh_op = gr.Slider(0.0, 1.0, value=0.3, step=0.05, label="Shadow Opacity")
                            t2_sh_blur = gr.Slider(0, 30, value=10, step=1, label="Shadow Blur")
                            t2_sh_dx = gr.Slider(-100, 100, value=15, step=5, label="Shadow Offset X")
                            t2_sh_dy = gr.Slider(-100, 100, value=15, step=5, label="Shadow Offset Y")
                            t2_match_light = gr.Checkbox(label="Auto Match Subject Brightness", value=False)

                        t2_btn = gr.Button("Render Composition", variant="primary")

                    with gr.Column():
                        t2_output = gr.Image(type="pil", label="Composited Result")
                        t2_status = gr.Textbox(label="Status", interactive=False)

                t2_btn.click(
                    fn=process_tab2_composite,
                    inputs=[t2_fg, t2_bg, t2_model, t2_scale, t2_offx, t2_offy, t2_rot, t2_bg_blur, t2_sh_op, t2_sh_blur, t2_sh_dx, t2_sh_dy, t2_match_light],
                    outputs=[t2_output, t2_status]
                )

            # --------------------------------------------------
            # TAB 3: EDGE MATTING & RETOUCHING
            # --------------------------------------------------
            with gr.TabItem("✨ Edge Retouch & Defringe"):
                gr.Markdown("### Clean Cutout Halos, Smooth Fringes & Adjust Edges")
                with gr.Row():
                    with gr.Column():
                        t3_input = gr.Image(type="pil", label="Source Transparent Image (RGBA)")
                        t3_erode_dilate = gr.Slider(-20, 20, value=0, step=1, label="Erode (-) / Dilate (+) Edge")
                        t3_edge_blur = gr.Slider(0.0, 10.0, value=0.0, step=0.5, label="Edge Gaussian Blur")
                        t3_defringe = gr.Slider(0, 100, value=30, step=5, label="Defringe / Halo Cleanup Strength")
                        t3_mask_contrast = gr.Slider(0.5, 3.0, value=1.0, step=0.1, label="Alpha Mask Contrast Boost")
                        t3_btn = gr.Button("Apply Edge Retouching", variant="primary")

                    with gr.Column():
                        t3_output = gr.Image(type="pil", label="Retouched Result", format="png")
                        t3_status = gr.Textbox(label="Status", interactive=False)

                t3_btn.click(
                    fn=process_tab3_retouch,
                    inputs=[t3_input, t3_erode_dilate, t3_edge_blur, t3_defringe, t3_mask_contrast],
                    outputs=[t3_output, t3_status]
                )

            # --------------------------------------------------
            # TAB 4: IMAGE ENHANCER & PRESETS
            # --------------------------------------------------
            with gr.TabItem("🎨 Enhancers & Presets"):
                gr.Markdown("### Professional Image Grading, Adjustments & Color Presets")
                with gr.Row():
                    with gr.Column():
                        t4_input = gr.Image(type="pil", label="Input Image")
                        t4_preset = gr.Dropdown(
                            ["None", "Vintage Warm", "Cyberpunk Glow", "Cinematic Cool", "High Contrast B&W", "Portrait Soft"],
                            value="None",
                            label="Filter Preset"
                        )
                        t4_bright = gr.Slider(0.2, 2.0, value=1.0, step=0.05, label="Brightness")
                        t4_contrast = gr.Slider(0.2, 2.0, value=1.0, step=0.05, label="Contrast")
                        t4_sat = gr.Slider(0.0, 2.0, value=1.0, step=0.05, label="Saturation")
                        t4_sharp = gr.Slider(0.0, 3.0, value=1.0, step=0.1, label="Sharpness")
                        t4_temp = gr.Slider(-5, 5, value=0, step=1, label="Temperature (Cool <-> Warm)")
                        t4_vignette = gr.Slider(0.0, 1.0, value=0.0, step=0.05, label="Vignette Effect")
                        t4_btn = gr.Button("Apply Enhancements", variant="primary")

                    with gr.Column():
                        t4_output = gr.Image(type="pil", label="Enhanced Result")
                        t4_status = gr.Textbox(label="Status", interactive=False)

                t4_btn.click(
                    fn=process_tab4_enhancer,
                    inputs=[t4_input, t4_preset, t4_bright, t4_contrast, t4_sat, t4_sharp, t4_temp, t4_vignette],
                    outputs=[t4_output, t4_status]
                )

            # --------------------------------------------------
            # TAB 5: RESIZER & SOCIAL TEMPLATES
            # --------------------------------------------------
            with gr.TabItem("📐 Resizer & Templates"):
                gr.Markdown("### Smart Resizer, Format Converter & Social Media Cropper")
                with gr.Row():
                    with gr.Column():
                        t5_input = gr.Image(type="pil", label="Input Image")
                        t5_template = gr.Dropdown(
                            list(SOCIAL_TEMPLATES.keys()),
                            value="Custom",
                            label="Social Media Preset"
                        )
                        t5_w = gr.Number(value=1080, label="Target Width (px)")
                        t5_h = gr.Number(value=1080, label="Target Height (px)")
                        t5_crop = gr.Radio(["Fit / Pad", "Center Crop", "Stretch"], value="Center Crop", label="Resizing Mode")
                        t5_fmt = gr.Dropdown(["PNG", "JPG", "WEBP"], value="PNG", label="Output Format")
                        t5_quality = gr.Slider(10, 100, value=90, step=5, label="Export Quality")
                        t5_btn = gr.Button("Resize & Convert", variant="primary")

                    with gr.Column():
                        t5_output_img = gr.Image(type="pil", label="Resized Preview")
                        t5_output_file = gr.File(label="Download File")
                        t5_status = gr.Textbox(label="Status / Output Details", interactive=False)

                t5_template.change(
                    fn=update_resizer_dimensions,
                    inputs=[t5_template],
                    outputs=[t5_w, t5_h]
                )

                t5_btn.click(
                    fn=process_tab5_resizer,
                    inputs=[t5_input, t5_template, t5_w, t5_h, t5_crop, t5_fmt, t5_quality],
                    outputs=[t5_output_img, t5_output_file, t5_status]
                )

            # --------------------------------------------------
            # TAB 6: BATCH PROCESSOR
            # --------------------------------------------------
            with gr.TabItem("📦 Batch Processor"):
                gr.Markdown("### Process Multiple Images in Parallel and Download as ZIP")
                with gr.Row():
                    with gr.Column():
                        t6_files = gr.File(file_count="multiple", label="Upload Multiple Images")
                        t6_model = gr.Dropdown(["u2netp", "u2net"], value="u2netp", label="BG Model")
                        t6_preset = gr.Dropdown(
                            ["None", "Vintage Warm", "Cyberpunk Glow", "Cinematic Cool", "High Contrast B&W"],
                            value="None",
                            label="Apply Filter Preset to Batch"
                        )
                        t6_btn = gr.Button("Run Batch Process", variant="primary")

                    with gr.Column():
                        t6_zip_out = gr.File(label="Download Output (ZIP)")
                        t6_status = gr.Textbox(label="Status Log", interactive=False)

                t6_btn.click(
                    fn=process_tab6_batch,
                    inputs=[t6_files, t6_model, t6_preset],
                    outputs=[t6_zip_out, t6_status]
                )

            # --------------------------------------------------
            # TAB 7: IMAGE INSPECTOR & PALETTE
            # --------------------------------------------------
            with gr.TabItem("🔍 Inspector & Color Palette"):
                gr.Markdown("### Extract Dominant Color Palette & Inspect Image Metadata")
                with gr.Row():
                    with gr.Column():
                        t7_input = gr.Image(type="pil", label="Input Image")
                        t7_btn = gr.Button("Analyze Image", variant="primary")

                    with gr.Column():
                        t7_report = gr.Markdown(label="Analysis Report")
                        t7_palette = gr.Image(type="pil", label="Dominant Color Palette")

                t7_btn.click(
                    fn=process_tab7_inspector,
                    inputs=[t7_input],
                    outputs=[t7_report, t7_palette]
                )

    return demo


# ======================================================
# 11. DEPLOYMENT LAUNCHER FOR RENDER
# ======================================================

if __name__ == "__main__":
    app_demo = build_app()
    
    # Read dynamic port provided by Render
    port = int(os.environ.get("PORT", 7860))
    
    # Queue concurrency set to 1 thread to avoid RAM overload on free tier
    app_demo.queue(default_concurrency_limit=1).launch(
        server_name="0.0.0.0",
        server_port=port
    )
