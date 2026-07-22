"""
================================================================================
                    SHADOW FLAMEZ AI STUDIO PRO V5.0
               Enterprise Transparency & Image Engine
================================================================================
Description: Comprehensive Gradio Studio Application for AI Neural Background
             Removal, HSV Chroma Keying, FX Filtering, Watermarking, and Batch
             Processing. Built with OpenCV, PIL, RemBG, and Gradio.
================================================================================
"""

import os
os.environ["GRADIO_SERVER_NAME"] = "0.0.0.0"
os.environ["GRADIO_SERVER_PORT"] = os.environ.get("PORT", "10000")
import sys
import time
import math
import io
import zipfile
import logging
from typing import Tuple, List, Optional, Dict, Union, Any
from dataclasses import dataclass, field
from datetime import datetime

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw, ImageFont
import gradio as gr
from rembg import remove, new_session

# ==============================================================================
# 1. LOGGING & SYSTEM DIAGNOSTICS INITIALIZATION
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ShadowFlamezStudio")


@dataclass
class PerformanceMetric:
    """Dataclass to record processing runtime and operational statistics."""
    task_name: str
    execution_time: float
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    status: str = "SUCCESS"
    details: str = ""


class DiagnosticsManager:
    """Manages system metrics, performance history, and diagnostic logging."""
    def __init__(self):
        self.metrics_history: List[PerformanceMetric] = []
        self.total_processed_count: int = 0
        self.start_time: float = time.time()

    def record_task(self, task_name: str, exec_time: float, status: str = "SUCCESS", details: str = ""):
        metric = PerformanceMetric(
            task_name=task_name,
            execution_time=exec_time,
            status=status,
            details=details
        )
        self.metrics_history.append(metric)
        if status == "SUCCESS":
            self.total_processed_count += 1
        logger.info(f"Task '{task_name}' executed in {exec_time:.3f}s with status [{status}]")

    def get_uptime(self) -> str:
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def generate_report_html(self) -> str:
        avg_time = (
            sum(m.execution_time for m in self.metrics_history) / len(self.metrics_history)
            if self.metrics_history else 0.0
        )
        html = f"""
        <div style="background: #12121a; border: 1px solid #2a2a3d; padding: 15px; border-radius: 10px; color: #e0e0e0; font-family: monospace;">
            <h4 style="color: #00ffff; margin-top: 0;">📊 System Health & Analytics</h4>
            <p>⏱️ <b>System Uptime:</b> {self.get_uptime()}</p>
            <p>🖼️ <b>Total Images Processed:</b> {self.total_processed_count}</p>
            <p>⚡ <b>Average Processing Time:</b> {avg_time:.2f} seconds</p>
            <hr style="border: 0; border-top: 1px solid #333;">
            <h5 style="color: #ff0055; margin-bottom: 5px;">Execution Log (Last 5 Tasks):</h5>
            <ul style="padding-left: 20px; font-size: 0.9em;">
        """
        for m in reversed(self.metrics_history[-5:]):
            color = "#00ff66" if m.status == "SUCCESS" else "#ff0055"
            html += f'<li><span style="color:{color};">[{m.timestamp}]</span> <b>{m.task_name}</b> - {m.execution_time:.2f}s ({m.details})</li>'
        html += "</ul></div>"
        return html


diagnostics = DiagnosticsManager()

# ==============================================================================
# 2. BRANDING & UI STYLING CONSTANTS (CSS, SVG, HTML TEMPLATES)
# ==============================================================================

STUDIO_CSS = """
@keyframes neon-pulse {
    0% { filter: drop-shadow(0 0 5px #ff0055) drop-shadow(0 0 15px #ff0055); }
    50% { filter: drop-shadow(0 0 18px #00ffff) drop-shadow(0 0 35px #7a00ff); }
    100% { filter: drop-shadow(0 0 5px #ff0055) drop-shadow(0 0 15px #ff0055); }
}

@keyframes gradient-shift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes border-glow {
    0% { border-color: #ff0055; }
    50% { border-color: #00ffff; }
    100% { border-color: #ff0055; }
}

.studio-header {
    background: linear-gradient(-45deg, #0a0a0f, #141428, #1a0f2e, #0f243a);
    background-size: 400% 400%;
    animation: gradient-shift 12s ease infinite;
    padding: 30px;
    border-radius: 16px;
    border: 1px solid #2e2e4a;
    text-align: center;
    margin-bottom: 25px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
}

.logo-container {
    display: inline-block;
    animation: neon-pulse 3.5s infinite alternate;
}

.studio-title {
    font-family: 'Impact', 'Arial Black', sans-serif;
    font-size: 2.8em;
    font-weight: 900;
    margin: 12px 0 6px 0;
    background: linear-gradient(90deg, #ff0055, #ff5500, #ffff00, #00ffff, #7a00ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 2.5px;
}

.studio-subtitle {
    color: #9090b8;
    font-size: 1.15em;
    font-weight: 500;
    margin: 0;
    letter-spacing: 0.5px;
}

.status-badge {
    padding: 14px 18px;
    border-radius: 10px;
    background: #12121e;
    border-left: 6px solid #00ffff;
    color: #ffffff;
    font-weight: 600;
    font-family: 'Courier New', monospace;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

.studio-footer {
    text-align: center;
    padding: 20px;
    color: #707090;
    font-size: 0.9em;
    border-top: 1px solid #202035;
    margin-top: 30px;
}
"""

STUDIO_HEADER_HTML = """
<div class="studio-header">
    <div class="logo-container">
        <svg width="90" height="90" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="flameGradMain" x1="0%" y1="100%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#ff0055;stop-opacity:1" />
                    <stop offset="50%" style="stop-color:#7a00ff;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#00ffff;stop-opacity:1" />
                </linearGradient>
            </defs>
            <circle cx="50" cy="50" r="46" fill="none" stroke="url(#flameGradMain)" stroke-width="4" stroke-dasharray="10 5"/>
            <path d="M50 12 C28 35, 18 55, 34 78 C44 90, 56 90, 66 78 C82 55, 72 35, 50 12 Z" fill="url(#flameGradMain)" opacity="0.85"/>
            <path d="M50 28 C36 44, 30 58, 40 72 C46 80, 54 80, 60 72 C70 58, 64 44, 50 28 Z" fill="#0a0a0f"/>
            <path d="M50 44 C42 54, 38 62, 45 70 C48 75, 52 75, 55 70 C62 62, 58 54, 50 44 Z" fill="url(#flameGradMain)"/>
        </svg>
    </div>
    <div class="studio-title">SHADOW FLAMEZ STUDIO</div>
    <div class="studio-subtitle">⚡ Enterprise AI Neural Transparency, FX & Compositing Suite v5.0</div>
</div>
"""

STUDIO_FOOTER_HTML = """
<div class="studio-footer">
    🔥 <b>Shadow Flamez AI Studio Pro v5.0</b> | High-Performance Python & OpenCV Image Processing Engine
</div>
"""

# ==============================================================================
# 3. UTILITY & IMAGE CONVERSION ENGINE
# ==============================================================================


class ImageUtils:
    """Provides essential utility functions for image conversions and calculations."""

    @staticmethod
    def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
        """Converts PIL Image (RGB/RGBA) to OpenCV NumPy array (BGR/BGRA)."""
        if pil_image is None:
            raise ValueError("Input PIL Image cannot be None.")

        np_img = np.array(pil_image)
        if np_img.ndim == 2:  # Grayscale
            return cv2.cvtColor(np_img, cv2.COLOR_GRAY2BGR)
        elif np_img.shape[2] == 3:  # RGB
            return cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
        elif np_img.shape[2] == 4:  # RGBA
            return cv2.cvtColor(np_img, cv2.COLOR_RGBA2BGRA)
        return np_img

    @staticmethod
    def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
        """Converts OpenCV NumPy array (BGR/BGRA) to PIL Image (RGB/RGBA)."""
        if cv2_image is None:
            raise ValueError("Input OpenCV array cannot be None.")

        if cv2_image.ndim == 2:  # Grayscale
            return Image.fromarray(cv2_image)
        elif cv2_image.shape[2] == 3:  # BGR
            rgb = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb)
        elif cv2_image.shape[2] == 4:  # BGRA
            rgba = cv2.cvtColor(cv2_image, cv2.COLOR_BGRA2RGBA)
            return Image.fromarray(rgba)
        return Image.fromarray(cv2_image)

    @staticmethod
    def ensure_rgba(image: Union[Image.Image, np.ndarray]) -> Image.Image:
        """Ensures the image is returned as a 4-channel RGBA PIL Image."""
        if isinstance(image, np.ndarray):
            image = ImageUtils.cv2_to_pil(image)

        if image.mode != "RGBA":
            return image.convert("RGBA")
        return image

    @staticmethod
    def resize_aspect_ratio(
        image: Image.Image,
        max_width: int = 1920,
        max_height: int = 1080
    ) -> Image.Image:
        """Resizes an image preserving aspect ratio within bounding box limits."""
        w, h = image.size
        ratio = min(max_width / float(w), max_height / float(h))
        if ratio < 1.0:
            new_size = (int(w * ratio), int(h * ratio))
            return image.resize(new_size, Image.Resampling.LANCZOS)
        return image


# ==============================================================================
# 4. CHECKERBOARD & PATTERN GENERATOR ENGINE
# ==============================================================================


class CheckerboardGenerator:
    """Generates dynamic checkerboard patterns for visualizing transparent backgrounds."""

    @staticmethod
    def create(
        width: int,
        height: int,
        square_size: int = 20,
        color1: Tuple[int, int, int] = (200, 200, 200),
        color2: Tuple[int, int, int] = (240, 240, 240)
    ) -> Image.Image:
        """Creates a high-contrast checkerboard background grid."""
        width = max(1, width)
        height = max(1, height)
        square_size = max(2, square_size)

        bg = np.zeros((height, width, 4), dtype=np.uint8)

        for y in range(0, height, square_size):
            for x in range(0, width, square_size):
                if (x // square_size + y // square_size) % 2 == 0:
                    bg[y:y + square_size, x:x + square_size] = [color1[0], color1[1], color1[2], 255]
                else:
                    bg[y:y + square_size, x:x + square_size] = [color2[0], color2[1], color2[2], 255]

        return Image.fromarray(bg)


# ==============================================================================
# 5. NEURAL AI BACKGROUND REMOVAL ENGINE (REMBG INTEGRATION)
# ==============================================================================


class NeuralEngine:
    """Encapsulates RemBG session models for AI-driven background extraction."""

    def __init__(self):
        self.sessions: Dict[str, Any] = {}
        # Pre-load full precision u2net model for maximum accuracy
        self._get_session("u2net")

    def _get_session(self, model_name: str):
        if model_name not in self.sessions:
            logger.info(f"Loading RemBG Session model: [{model_name}]...")
            try:
                self.sessions[model_name] = new_session(model_name)
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}. Falling back to u2net.")
                if "u2net" not in self.sessions:
                    self.sessions["u2net"] = new_session("u2net")
                return self.sessions["u2net"]
        return self.sessions[model_name]

    def remove_background(
        self,
        pil_image: Image.Image,
        model_name: str = "u2net",
        alpha_matting: bool = False,
        foreground_threshold: int = 240,
        background_threshold: int = 10
    ) -> Image.Image:
        """Performs AI neural background removal returning a 4-channel RGBA PIL Image."""
        session = self._get_session(model_name)

        output = remove(
            pil_image,
            session=session,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=foreground_threshold,
            alpha_matting_background_threshold=background_threshold
        )
        return ImageUtils.ensure_rgba(output)


neural_engine = NeuralEngine()

# ==============================================================================
# 6. OPENCV FAST CHROMA KEYING ENGINE (GREEN/BLUE SCREEN)
# ==============================================================================


class ChromaKeyEngine:
    """High-speed HSV color thresholding engine for Green, Blue, and custom color screens."""

    @staticmethod
    def hex_to_hsv(hex_color: str) -> Tuple[int, int, int]:
        """Converts HEX color string to OpenCV HSV representation."""
        hex_val = hex_color.lstrip('#')
        if len(hex_val) != 6:
            hex_val = "00FF00"  # Default Green
        r = int(hex_val[0:2], 16)
        g = int(hex_val[2:4], 16)
        b = int(hex_val[4:6], 16)

        bgr = np.uint8([[[b, g, r]]])
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        return int(hsv[0][0][0]), int(hsv[0][0][1]), int(hsv[0][0][2])

    @staticmethod
    def process_keying(
        pil_image: Image.Image,
        screen_type: str = "Green Screen",
        custom_hex: str = "#00FF00",
        hue_tolerance: int = 15,
        sat_min: int = 40,
        val_min: int = 40,
        feather_radius: int = 2,
        spill_suppression: bool = True
    ) -> Image.Image:
        """Executes HSV color keying, mask generation, feathering, and alpha merging."""
        img_np = np.array(ImageUtils.ensure_rgba(pil_image))
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        # Determine target HSV center
        if screen_type == "Green Screen":
            target_h, target_s, target_v = 60, 200, 200
        elif screen_type == "Blue Screen":
            target_h, target_s, target_v = 120, 200, 200
        else:
            target_h, target_s, target_v = ChromaKeyEngine.hex_to_hsv(custom_hex)

        # Calculate HSV bounding range
        lower_h = max(0, target_h - hue_tolerance)
        upper_h = min(179, target_h + hue_tolerance)

        lower_bound = np.array([lower_h, sat_min, val_min], dtype=np.uint8)
        upper_bound = np.array([upper_h, 255, 255], dtype=np.uint8)

        # Create mask of background pixels
        mask = cv2.inRange(hsv, lower_bound, upper_bound)

        # Invert mask: Subject = 255 (Opaque), Background = 0 (Transparent)
        subject_mask = cv2.bitwise_not(mask)

        # Apply Spill Suppression (Remove color cast from edges)
        if spill_suppression and screen_type == "Green Screen":
            b_ch, g_ch, r_ch = cv2.split(img_bgr)
            # Limit Green channel intensity to max of Blue and Red
            max_bg_r = cv2.max(b_ch, r_ch)
            g_ch = cv2.min(g_ch, max_bg_r)
            img_bgr = cv2.merge([b_ch, g_ch, r_ch])

        # Apply Feathering (Gaussian Blur on Alpha Mask)
        if feather_radius > 0:
            ksize = feather_radius * 2 + 1
            subject_mask = cv2.GaussianBlur(subject_mask, (ksize, ksize), 0)

        # Merge BGR channels with new Alpha mask
        b_ch, g_ch, r_ch = cv2.split(img_bgr)
        bgra = cv2.merge([b_ch, g_ch, r_ch, subject_mask])

        return ImageUtils.cv2_to_pil(bgra)


# ==============================================================================
# 7. IMAGE EFFECTS & ARTISTIC FILTERS ENGINE
# ==============================================================================


class ImageEffectsEngine:
    """Applies post-processing color grading, sharpening, and artistic filters."""

    @staticmethod
    def adjust_colors(
        pil_image: Image.Image,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0
    ) -> Image.Image:
        """Applies basic color corrections (Brightness, Contrast, Saturation, Sharpness)."""
        img = pil_image.copy()

        if brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        if saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(saturation)
        if sharpness != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(sharpness)

        return img

    @staticmethod
    def apply_cyberpunk_filter(pil_image: Image.Image) -> Image.Image:
        """Applies a high-contrast Cyberpunk Teal & Magenta color grade."""
        img_rgba = ImageUtils.ensure_rgba(pil_image)
        r, g, b, a = img_rgba.split()

        # Enhance Cyan in B/G and Pink/Magenta in R
        r = ImageEnhance.Brightness(r).enhance(1.2)
        b = ImageEnhance.Brightness(b).enhance(1.4)
        g = ImageEnhance.Contrast(g).enhance(0.9)

        merged = Image.merge("RGBA", (r, g, b, a))
        return ImageEnhance.Contrast(merged).enhance(1.25)

    @staticmethod
    def apply_neon_outline(
        pil_image: Image.Image,
        glow_color: str = "#00FFFF",
        thickness: int = 5
    ) -> Image.Image:
        """Generates a glowing neon outline around alpha subject boundaries."""
        rgba = ImageUtils.ensure_rgba(pil_image)
        alpha = rgba.split()[3]

        # Extract edge contour from alpha channel
        alpha_np = np.array(alpha)
        edges = cv2.Canny(alpha_np, 100, 200)

        if thickness > 1:
            kernel = np.ones((thickness, thickness), np.uint8)
            edges = cv2.dilate(edges, kernel, iterations=1)

        # Smooth edge glow
        edges_blur = cv2.GaussianBlur(edges, (15, 15), 0)

        # Colorize edge glow
        hex_val = glow_color.lstrip('#')
        gr_col = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))

        glow_bg = np.zeros((rgba.height, rgba.width, 4), dtype=np.uint8)
        glow_bg[edges_blur > 10] = [gr_col[0], gr_col[1], gr_col[2], 255]

        glow_pil = Image.fromarray(glow_bg).filter(ImageFilter.GaussianBlur(3))

        # Composite original subject over glow outline
        return Image.alpha_composite(glow_pil, rgba)


# ==============================================================================
# 8. COMPOSITING & BACKGROUND REPLACEMENT ENGINE
# ==============================================================================


class CompositingEngine:
    """Handles compositing of foreground RGBA layers over various background styles."""

    @staticmethod
    def create_gradient_background(
        width: int,
        height: int,
        color_start_hex: str = "#ff0055",
        color_end_hex: str = "#00ffff",
        angle: str = "Linear Diagonal"
    ) -> Image.Image:
        """Generates smooth multi-color linear or radial gradient backgrounds."""
        hex1 = color_start_hex.lstrip('#')
        hex2 = color_end_hex.lstrip('#')

        c1 = np.array([int(hex1[i:i+2], 16) for i in (0, 2, 4)], dtype=float)
        c2 = np.array([int(hex2[i:i+2], 16) for i in (0, 2, 4)], dtype=float)

        bg = np.zeros((height, width, 4), dtype=np.uint8)

        if angle == "Linear Vertical":
            for y in range(height):
                ratio = y / float(height)
                col = (1.0 - ratio) * c1 + ratio * c2
                bg[y, :] = [int(col[0]), int(col[1]), int(col[2]), 255]

        elif angle == "Linear Horizontal":
            for x in range(width):
                ratio = x / float(width)
                col = (1.0 - ratio) * c1 + ratio * c2
                bg[:, x] = [int(col[0]), int(col[1]), int(col[2]), 255]

        else:  # Diagonal
            for y in range(height):
                for x in range(width):
                    ratio = (x / float(width) + y / float(height)) / 2.0
                    col = (1.0 - ratio) * c1 + ratio * c2
                    bg[y, x] = [int(col[0]), int(col[1]), int(col[2]), 255]

        return Image.fromarray(bg)

    @staticmethod
    def composite_layers(
        foreground: Image.Image,
        bg_option: str = "Checkerboard Preview",
        solid_hex: str = "#0F3460",
        grad_start_hex: str = "#FF0055",
        grad_end_hex: str = "#00FFFF",
        grad_style: str = "Linear Diagonal",
        custom_bg_img: Optional[Image.Image] = None
    ) -> Image.Image:
        """Composites foreground RGBA subject onto user-selected background type."""
        fg_rgba = ImageUtils.ensure_rgba(foreground)
        w, h = fg_rgba.size

        if bg_option == "Transparent (PNG)":
            return fg_rgba

        elif bg_option == "Checkerboard Preview":
            bg = CheckerboardGenerator.create(w, h)
            return Image.alpha_composite(bg, fg_rgba)

        elif bg_option == "Solid Custom Color":
            hex_val = solid_hex.lstrip('#')
            rgb_col = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4)) + (255,)
            bg = Image.new("RGBA", (w, h), rgb_col)
            return Image.alpha_composite(bg, fg_rgba)

        elif bg_option == "Gradient Color":
            bg = CompositingEngine.create_gradient_background(
                w, h, grad_start_hex, grad_end_hex, grad_style
            )
            return Image.alpha_composite(bg, fg_rgba)

        elif bg_option == "Custom Background Image":
            if custom_bg_img is not None:
                bg_resized = custom_bg_img.convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
                return Image.alpha_composite(bg_resized, fg_rgba)
            else:
                # Fallback to checkerboard if no custom image was provided
                bg = CheckerboardGenerator.create(w, h)
                return Image.alpha_composite(bg, fg_rgba)

        return fg_rgba


# ==============================================================================
# 9. BRANDING & WATERMARK ENGINE
# ==============================================================================


class WatermarkEngine:
    """Overlays custom text signatures or image logos onto rendered compositions."""

    @staticmethod
    def apply_text_watermark(
        image: Image.Image,
        text: str = "SHADOW FLAMEZ STUDIO",
        position: str = "Bottom Right",
        opacity: float = 0.7,
        font_size: int = 32,
        text_color: str = "#FFFFFF"
    ) -> Image.Image:
        """Draws branded text watermark onto image canvas with customizable position and opacity."""
        if not text.strip():
            return image

        base = ImageUtils.ensure_rgba(image).copy()
        txt_layer = Image.new("RGBA", base.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        # Load font safely or default
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

        # Calculate bounding box of text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        w, h = base.size
        margin = 20

        if position == "Top Left":
            pos = (margin, margin)
        elif position == "Top Right":
            pos = (w - text_w - margin, margin)
        elif position == "Center":
            pos = ((w - text_w) // 2, (h - text_h) // 2)
        elif position == "Bottom Left":
            pos = (margin, h - text_h - margin)
        else:  # Bottom Right
            pos = (w - text_w - margin, h - text_h - margin)

        hex_val = text_color.lstrip('#')
        rgb = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
        alpha_val = int(255 * opacity)

        draw.text(pos, text, font=font, fill=(rgb[0], rgb[1], rgb[2], alpha_val))

        return Image.alpha_composite(base, txt_layer)


# ==============================================================================
# 10. BATCH PROCESSING ENGINE
# ==============================================================================


class BatchEngine:
    """Processes multiple image files sequentially and bundles outputs into a ZIP archive."""

    @staticmethod
    def process_batch(
        image_list: List[Any],
        processing_mode: str,
        bg_option: str,
        solid_color: str,
        progress=gr.Progress(track_tqdm=True)
    ) -> Tuple[List[Image.Image], str, str]:
        """Iterates over batch inputs, applies transparency, and builds a ZIP download package."""
        if not image_list:
            return [], None, "⚠️ No images provided for batch processing."

        start_time = time.time()
        processed_images: List[Image.Image] = []

        # Create temporary zip archive in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            total = len(image_list)

            for idx, img_data in enumerate(image_list):
                progress((idx + 1) / float(total), desc=f"Processing Image {idx+1}/{total}...")

                try:
                    # Convert input format
                    if isinstance(img_data, np.ndarray):
                        pil_img = ImageUtils.cv2_to_pil(img_data)
                    elif isinstance(img_data, str):
                        pil_img = Image.open(img_data)
                    else:
                        pil_img = img_data

                    # Apply removal mode
                    if processing_mode == "AI Neural Removal (rembg)":
                        fg = neural_engine.remove_background(pil_img, model_name="u2net")
                    else:
                        fg = ChromaKeyEngine.process_keying(pil_img, screen_type="Green Screen")

                    # Composite background
                    final_img = CompositingEngine.composite_layers(
                        foreground=fg,
                        bg_option=bg_option,
                        solid_hex=solid_color
                    )

                    processed_images.append(final_img)

                    # Save into ZIP
                    img_byte_arr = io.BytesIO()
                    final_img.save(img_byte_arr, format="PNG")
                    zip_file.writestr(f"shadow_flamez_out_{idx+1:03d}.png", img_byte_arr.getvalue())

                except Exception as e:
                    logger.error(f"Error processing batch item {idx+1}: {e}")

        zip_buffer.seek(0)
        
        # Save temporary zip file locally for download
        zip_path = os.path.join(os.getcwd(), "shadow_flamez_batch_export.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_buffer.getvalue())

        elapsed = round(time.time() - start_time, 2)
        diagnostics.record_task("Batch Processing Task", elapsed, details=f"Processed {len(processed_images)} images")

        status_msg = f"✅ Batch complete! Processed {len(processed_images)} images in {elapsed}s."
        return processed_images, zip_path, status_msg


# ==============================================================================
# 11. GRADIO INTERFACE EVENT CALLBACK HANDLERS
# ==============================================================================


def format_status_badge(message: str, status_type: str = "info") -> str:
    """Returns styled HTML status badge for UI response headers."""
    color_map = {
        "info": "#00ffff",
        "success": "#00ff66",
        "warning": "#ffaa00",
        "error": "#ff0055"
    }
    border_col = color_map.get(status_type, "#00ffff")
    return f'<div class="status-badge" style="border-left-color: {border_col};">⚡ STATUS: {message}</div>'


def single_image_pipeline(
    input_image: Optional[Image.Image],
    custom_bg_img: Optional[Image.Image],
    processing_mode: str,
    ai_model_name: str,
    bg_option: str,
    solid_color: str,
    grad_start: str,
    grad_end: str,
    grad_style: str,
    hue_tol: int,
    sat_min: int,
    feather_val: int,
    spill_suppress: bool,
    progress=gr.Progress(track_tqdm=True)
) -> Tuple[Optional[Image.Image], str]:
    """Primary pipeline handler for Single Image Studio Tab."""
    if input_image is None:
        return None, format_status_badge("Please upload a source image first.", "warning")

    start_time = time.time()
    progress(0.1, desc="Initializing Engine...")

    try:
        # Step 1: Execute Selected Background Removal Engine
        progress(0.3, desc=f"Executing {processing_mode}...")
        if processing_mode == "AI Neural Removal (rembg)":
            fg = neural_engine.remove_background(
                pil_image=input_image,
                model_name=ai_model_name
            )
        else:
            fg = ChromaKeyEngine.process_keying(
                pil_image=input_image,
                screen_type="Green Screen" if "Green" in processing_mode else "Blue Screen",
                hue_tolerance=hue_tol,
                sat_min=sat_min,
                feather_radius=feather_val,
                spill_suppression=spill_suppress
            )

        # Step 2: Composite Background Layer
        progress(0.7, desc="Applying Background Compositing Layer...")
        final_output = CompositingEngine.composite_layers(
            foreground=fg,
            bg_option=bg_option,
            solid_hex=solid_color,
            grad_start_hex=grad_start,
            grad_end_hex=grad_end,
            grad_style=grad_style,
            custom_bg_img=custom_bg_img
        )

        progress(1.0, desc="Rendering Complete!")
        elapsed = round(time.time() - start_time, 2)
        diagnostics.record_task("Single Image Pipeline", elapsed, details=f"Mode: {processing_mode} ({ai_model_name})")

        status_html = format_status_badge(
            f"Image rendered in {elapsed}s | Mode: {processing_mode} ({ai_model_name}) | Compositing: {bg_option}",
            "success"
        )
        return final_output, status_html

    except Exception as e:
        logger.error(f"Single Image Pipeline Failure: {e}")
        diagnostics.record_task("Single Image Pipeline", 0.0, status="ERROR", details=str(e))
        return None, format_status_badge(f"Error executing task: {str(e)}", "error")


def fx_pipeline(
    input_image: Optional[Image.Image],
    brightness: float,
    contrast: float,
    saturation: float,
    sharpness: float,
    fx_choice: str,
    glow_color: str,
    glow_thickness: int
) -> Tuple[Optional[Image.Image], str]:
    """Pipeline handler for FX & Color Grading Tab."""
    if input_image is None:
        return None, format_status_badge("Please upload an image to apply FX.", "warning")

    start_time = time.time()
    try:
        # Step 1: Color Adjustments
        img = ImageEffectsEngine.adjust_colors(
            input_image, brightness, contrast, saturation, sharpness
        )

        # Step 2: Artistic FX Selection
        if fx_choice == "Cyberpunk Teal & Pink":
            img = ImageEffectsEngine.apply_cyberpunk_filter(img)
        elif fx_choice == "Neon Glow Outline":
            img = ImageEffectsEngine.apply_neon_outline(img, glow_color, glow_thickness)

        elapsed = round(time.time() - start_time, 2)
        diagnostics.record_task("FX Pipeline", elapsed, details=f"FX: {fx_choice}")

        return img, format_status_badge(f"FX Applied successfully in {elapsed}s!", "success")

    except Exception as e:
        logger.error(f"FX Pipeline Failure: {e}")
        return None, format_status_badge(f"FX Processing failed: {str(e)}", "error")


def watermark_pipeline(
    input_image: Optional[Image.Image],
    text: str,
    position: str,
    opacity: float,
    font_size: int,
    text_color: str
) -> Tuple[Optional[Image.Image], str]:
    """Pipeline handler for Branding & Watermark Tab."""
    if input_image is None:
        return None, format_status_badge("Upload an image first.", "warning")

    try:
        res = WatermarkEngine.apply_text_watermark(
            image=input_image,
            text=text,
            position=position,
            opacity=opacity,
            font_size=font_size,
            text_color=text_color
        )
        return res, format_status_badge("Watermark applied successfully!", "success")
    except Exception as e:
        return None, format_status_badge(f"Watermark failure: {str(e)}", "error")


# ==============================================================================
# 12. MAIN GRADIO BLOCKS APPLICATION BUILDER
# ==============================================================================

def build_studio_app() -> gr.Blocks:
    """Constructs the multi-tab Gradio UI Blocks Application."""

    with gr.Blocks(title="Shadow Flamez AI Studio Pro v5.0", css=STUDIO_CSS, theme=gr.themes.Slate()) as demo:

        # Header Hero Banner
        gr.HTML(STUDIO_HEADER_HTML)

        # Studio Tabs
        with gr.Tabs():

            # ------------------------------------------------------------------
            # TAB 1: SINGLE IMAGE STUDIO
            # ------------------------------------------------------------------
            with gr.Tab("🔥 Single Image Studio"):
                with gr.Row():
                    # Control Column (Left)
                    with gr.Column(scale=1):
                        gr.Markdown("### 📥 Source Input & Removal Engine")
                        input_img = gr.Image(
                            type="pil",
                            label="Upload Source Image",
                            sources=["upload", "clipboard", "webcam"]
                        )

                        proc_mode = gr.Radio(
                            choices=[
                                "AI Neural Removal (rembg)",
                                "Fast Green Screen Keying",
                                "Fast Blue Screen Keying"
                            ],
                            value="AI Neural Removal (rembg)",
                            label="⚙️ Processing Engine"
                        )

                        ai_model_choice = gr.Dropdown(
                            choices=[
                                "u2net",
                                "isnet-general-use",
                                "u2netp"
                            ],
                            value="u2net",
                            label="🧠 AI Model Selection (Use u2net for detailed cutouts)"
                        )

                        with gr.Accordion("🎛️ Chroma Key Fine-Tuning Controls", open=False):
                            hue_tol = gr.Slider(5, 40, value=15, step=1, label="Hue Tolerance")
                            sat_min = gr.Slider(10, 150, value=40, step=5, label="Min Saturation Threshold")
                            feather_slider = gr.Slider(0, 10, value=2, step=1, label="Edge Feathering Radius")
                            spill_suppress = gr.Checkbox(value=True, label="Enable Spill Suppression")

                        gr.Markdown("### 🎨 Background Compositing")
                        bg_style = gr.Radio(
                            choices=[
                                "Checkerboard Preview",
                                "Transparent (PNG)",
                                "Solid Custom Color",
                                "Gradient Color",
                                "Custom Background Image"
                            ],
                            value="Checkerboard Preview",
                            label="Background Mode"
                        )

                        with gr.Accordion("🖌️ Custom Background Settings", open=True):
                            solid_picker = gr.ColorPicker(value="#0F3460", label="Solid Color Picker")

                            with gr.Row():
                                grad_start_picker = gr.ColorPicker(value="#FF0055", label="Gradient Start")
                                grad_end_picker = gr.ColorPicker(value="#00FFFF", label="Gradient End")

                            grad_style_dropdown = gr.Dropdown(
                                choices=["Linear Diagonal", "Linear Vertical", "Linear Horizontal"],
                                value="Linear Diagonal",
                                label="Gradient Angle"
                            )

                            custom_bg_upload = gr.Image(
                                type="pil",
                                label="Upload Custom Background Image",
                                sources=["upload"]
                            )

                        btn_process = gr.Button("🔥 EXECUTE STUDIO RENDER", variant="primary", size="lg")

                    # Output Column (Right)
                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 Studio Render Result")
                        status_box = gr.HTML(format_status_badge("System Ready. Upload an image to start.", "info"))
                        output_img = gr.Image(type="pil", label="Rendered Output", format="png", interactive=False)

                # Connect Event Handler
                btn_process.click(
                    fn=single_image_pipeline,
                    inputs=[
                        input_img, custom_bg_upload, proc_mode, ai_model_choice, bg_style,
                        solid_picker, grad_start_picker, grad_end_picker,
                        grad_style_dropdown, hue_tol, sat_min, feather_slider, spill_suppress
                    ],
                    outputs=[output_img, status_box]
                )

            # ------------------------------------------------------------------
            # TAB 2: FX & COLOR GRADING STUDIO
            # ------------------------------------------------------------------
            with gr.Tab("✨ FX & Color Studio"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 🎛️ Color Adjustments & Filters")
                        fx_input_img = gr.Image(type="pil", label="Upload Image for FX")

                        bright_slider = gr.Slider(0.5, 2.0, value=1.0, step=0.05, label="Brightness")
                        contrast_slider = gr.Slider(0.5, 2.0, value=1.0, step=0.05, label="Contrast")
                        sat_slider = gr.Slider(0.0, 2.5, value=1.0, step=0.05, label="Saturation")
                        sharp_slider = gr.Slider(0.0, 3.0, value=1.0, step=0.1, label="Sharpness")

                        fx_preset = gr.Radio(
                            choices=["None", "Cyberpunk Teal & Pink", "Neon Glow Outline"],
                            value="None",
                            label="Artistic Preset FX"
                        )

                        with gr.Accordion("🚨 Neon Glow Settings", open=False):
                            glow_color_picker = gr.ColorPicker(value="#00FFFF", label="Glow Color")
                            glow_thick_slider = gr.Slider(1, 15, value=5, step=1, label="Glow Thickness")

                        btn_fx = gr.Button("✨ APPLY FX & FILTERS", variant="primary")

                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 Filtered Result")
                        fx_status = gr.HTML(format_status_badge("FX Engine Ready.", "info"))
                        fx_output_img = gr.Image(type="pil", label="FX Output", format="png")

                btn_fx.click(
                    fn=fx_pipeline,
                    inputs=[
                        fx_input_img, bright_slider, contrast_slider,
                        sat_slider, sharp_slider, fx_preset,
                        glow_color_picker, glow_thick_slider
                    ],
                    outputs=[fx_output_img, fx_status]
                )

            # ------------------------------------------------------------------
            # TAB 3: BRANDING & WATERMARK STUDIO
            # ------------------------------------------------------------------
            with gr.Tab("🏷️ Branding & Watermark"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### ✍️ Watermark Settings")
                        wm_input_img = gr.Image(type="pil", label="Upload Image")

                        wm_text = gr.Textbox(value="SHADOW FLAMEZ STUDIO", label="Watermark Text")
                        wm_pos = gr.Dropdown(
                            choices=["Top Left", "Top Right", "Center", "Bottom Left", "Bottom Right"],
                            value="Bottom Right",
                            label="Overlay Position"
                        )
                        wm_opacity = gr.Slider(0.1, 1.0, value=0.7, step=0.05, label="Opacity")
                        wm_size = gr.Slider(12, 72, value=32, step=2, label="Font Size")
                        wm_color = gr.ColorPicker(value="#FFFFFF", label="Text Color")

                        btn_wm = gr.Button("🏷️ APPLY WATERMARK", variant="primary")

                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 Branded Output")
                        wm_status = gr.HTML(format_status_badge("Watermark Engine Ready.", "info"))
                        wm_output_img = gr.Image(type="pil", label="Watermarked Output")

                btn_wm.click(
                    fn=watermark_pipeline,
                    inputs=[wm_input_img, wm_text, wm_pos, wm_opacity, wm_size, wm_color],
                    outputs=[wm_output_img, wm_status]
                )

            # ------------------------------------------------------------------
            # TAB 4: BATCH PROCESSING STUDIO
            # ------------------------------------------------------------------
            with gr.Tab("📦 Batch Processing"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📁 Batch Upload Queue")
                        batch_files = gr.File(file_count="multiple", label="Upload Multiple Images")

                        batch_mode = gr.Radio(
                            choices=["AI Neural Removal (rembg)", "Fast Green Screen Keying"],
                            value="AI Neural Removal (rembg)",
                            label="Batch Removal Mode"
                        )

                        batch_bg = gr.Radio(
                            choices=["Transparent (PNG)", "Checkerboard Preview", "Solid Custom Color"],
                            value="Transparent (PNG)",
                            label="Batch Background"
                        )
                        batch_color = gr.ColorPicker(value="#0F3460", label="Solid Background Color")

                        btn_batch = gr.Button("📦 PROCESS BATCH QUEUE", variant="primary", size="lg")

                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 Batch Output Gallery & Download")
                        batch_status = gr.HTML(format_status_badge("Batch Queue Empty.", "info"))
                        batch_gallery = gr.Gallery(label="Batch Output Gallery", columns=3)
                        batch_zip_file = gr.File(label="Download Processed ZIP Archive")

                btn_batch.click(
                    fn=BatchEngine.process_batch,
                    inputs=[batch_files, batch_mode, batch_bg, batch_color],
                    outputs=[batch_gallery, batch_zip_file, batch_status]
                )

            # ------------------------------------------------------------------
            # TAB 5: SYSTEM DIAGNOSTICS & ANALYTICS
            # ------------------------------------------------------------------
            with gr.Tab("📊 System Diagnostics"):
                gr.Markdown("### 📈 Real-Time Diagnostics & Performance Metrics")
                diag_html = gr.HTML(diagnostics.generate_report_html())
                btn_refresh_diag = gr.Button("🔄 REFRESH DIAGNOSTICS")

                btn_refresh_diag.click(
                    fn=lambda: diagnostics.generate_report_html(),
                    inputs=[],
                    outputs=[diag_html]
                )

        # Footer
        gr.HTML(STUDIO_FOOTER_HTML)

    return demo


# ==============================================================================
# 13. APPLICATION ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    # Get port assigned by Render (defaults to 10000)
    port = int(os.environ.get("PORT", 10000))
    
    app = build_studio_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        show_error=True
    )
