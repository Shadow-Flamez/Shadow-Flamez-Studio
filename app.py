"""
================================================================================
                SHADOW FLAMEZ AI STUDIO PRO V5.0 (ENTERPRISE EDITION)
               Neural AI Transparency, Compositing & FX Engine
================================================================================
Description: Fully optimized, highly scalable Gradio Studio Application for AI
             Neural Background Removal, HSV Chroma Keying, FX Filtering,
             Watermarking, Real-time Diagnostics, and Batch Processing.
================================================================================
"""

# ==============================================================================
# 0. ENVIRONMENT & HARDWARE ACCELERATION CONFIGURATION
# ==============================================================================
import os

# Set environment variables immediately before any heavy C/C++ libraries import
os.environ["ORT_LOGGING_LEVEL"] = "3"  # Suppress ONNX non-fatal C++ warnings
os.environ["ONNXRUNTIME_EXECUTION_PROVIDERS"] = "[CPUExecutionProvider]"  # Force clean CPU execution on cloud containers
os.environ["GRADIO_SERVER_NAME"] = "0.0.0.0"
os.environ["GRADIO_SERVER_PORT"] = os.environ.get("PORT", "10000")
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import sys
import time
import math
import io
import gc
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
    """Manages system metrics, performance history, memory tracking, and diagnostic logging."""
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
        
        success_rate = (
            (sum(1 for m in self.metrics_history if m.status == "SUCCESS") / len(self.metrics_history) * 100)
            if self.metrics_history else 100.0
        )

        html = f"""
        <div class="diag-container">
            <div class="diag-header">
                <h4>📊 System Health & Performance Analytics</h4>
                <span class="diag-badge">OPERATIONAL</span>
            </div>
            <div class="diag-grid">
                <div class="diag-card">
                    <span class="diag-label">⏱️ System Uptime</span>
                    <span class="diag-value">{self.get_uptime()}</span>
                </div>
                <div class="diag-card">
                    <span class="diag-label">🖼️ Total Processed</span>
                    <span class="diag-value">{self.total_processed_count} Images</span>
                </div>
                <div class="diag-card">
                    <span class="diag-label">⚡ Avg Latency</span>
                    <span class="diag-value">{avg_time:.2f}s</span>
                </div>
                <div class="diag-card">
                    <span class="diag-label">🎯 Success Rate</span>
                    <span class="diag-value">{success_rate:.1f}%</span>
                </div>
            </div>
            <hr class="diag-divider">
            <h5 style="color: #ff0055; margin-bottom: 10px;">📋 Execution Log (Last 8 Tasks):</h5>
            <ul class="diag-log-list">
        """
        for m in reversed(self.metrics_history[-8:]):
            color = "#00ff66" if m.status == "SUCCESS" else "#ff0055"
            html += f'<li><span style="color:{color};">[{m.timestamp}]</span> <b>{m.task_name}</b> - {m.execution_time:.2f}s <span style="opacity:0.7">({m.details})</span></li>'
        html += "</ul></div>"
        return html


diagnostics = DiagnosticsManager()

# ==============================================================================
# 2. BRANDING & BACKLIT ANIMATED UI CSS STYLING
# ==============================================================================

STUDIO_CSS = """
/* Keyframe Animations */
@keyframes neon-pulse {
    0% { filter: drop-shadow(0 0 5px #ff0055) drop-shadow(0 0 15px #ff0055); }
    50% { filter: drop-shadow(0 0 20px #00ffff) drop-shadow(0 0 35px #7a00ff); }
    100% { filter: drop-shadow(0 0 5px #ff0055) drop-shadow(0 0 15px #ff0055); }
}

@keyframes gradient-shift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes backlit-pulse {
    0% { box-shadow: 0 0 15px rgba(255, 0, 85, 0.4), 0 0 30px rgba(0, 255, 255, 0.2); }
    50% { box-shadow: 0 0 25px rgba(0, 255, 255, 0.6), 0 0 50px rgba(122, 0, 255, 0.4); }
    100% { box-shadow: 0 0 15px rgba(255, 0, 85, 0.4), 0 0 30px rgba(0, 255, 255, 0.2); }
}

@keyframes float-gentle {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-4px); }
    100% { transform: translateY(0px); }
}

/* Global Container Improvements */
.gradio-container {
    background: #08080e !important;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
}

/* Backlit Hover Effects on Buttons */
button.primary, .gr-button-primary {
    background: linear-gradient(135deg, #ff0055, #7a00ff) !important;
    border: 1px solid #ff0055 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1) !important;
    position: relative !important;
    overflow: hidden !important;
    border-radius: 10px !important;
}

button.primary:hover, .gr-button-primary:hover {
    transform: translateY(-2px) scale(1.01) !important;
    background: linear-gradient(135deg, #ff0066, #00ffff) !important;
    border-color: #00ffff !important;
    box-shadow: 0 0 25px rgba(0, 255, 255, 0.8), 0 0 50px rgba(255, 0, 85, 0.6), inset 0 0 15px rgba(255, 255, 255, 0.4) !important;
}

button.secondary, .gr-button-secondary {
    background: #141424 !important;
    border: 1px solid #2e2e4d !important;
    color: #00ffff !important;
    transition: all 0.35s ease !important;
    border-radius: 10px !important;
}

button.secondary:hover, .gr-button-secondary:hover {
    border-color: #00ffff !important;
    box-shadow: 0 0 20px rgba(0, 255, 255, 0.4) !important;
    transform: translateY(-2px) !important;
}

/* Cards & Panel Backlit Hover FX */
.gr-box, .gr-block, .gr-card, .gr-panel, .gr-form {
    background: #0e0e18 !important;
    border: 1px solid #1f1f35 !important;
    border-radius: 14px !important;
    transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

.gr-box:hover, .gr-block:hover, .gr-card:hover, .gr-panel:hover {
    border-color: rgba(0, 255, 255, 0.4) !important;
    box-shadow: 0 0 20px rgba(0, 255, 255, 0.15), 0 0 40px rgba(122, 0, 255, 0.1) !important;
}

/* Interactive Image Components Backlit FX */
.gr-image, .gradio-image {
    border-radius: 12px !important;
    transition: all 0.4s ease !important;
}

.gr-image:hover, .gradio-image:hover {
    box-shadow: 0 0 30px rgba(0, 255, 255, 0.35), 0 0 15px rgba(255, 0, 85, 0.25) !important;
    border-color: #00ffff !important;
}

/* Header Styling */
.studio-header {
    background: linear-gradient(-45deg, #07070c, #121226, #1b0c2e, #0c1d2e);
    background-size: 400% 400%;
    animation: gradient-shift 12s ease infinite;
    padding: 35px 25px;
    border-radius: 20px;
    border: 1px solid #2e2e4a;
    text-align: center;
    margin-bottom: 25px;
    box-shadow: 0 15px 50px rgba(0, 0, 0, 0.8), inset 0 0 20px rgba(0, 255, 255, 0.1);
    position: relative;
}

.studio-header:hover {
    animation: gradient-shift 8s ease infinite, backlit-pulse 4s infinite alternate;
}

.logo-container {
    display: inline-block;
    animation: neon-pulse 3.5s infinite alternate, float-gentle 4s ease-in-out infinite;
}

.studio-title {
    font-family: 'Impact', 'Arial Black', sans-serif;
    font-size: 3.2em;
    font-weight: 900;
    margin: 14px 0 6px 0;
    background: linear-gradient(90deg, #ff0055, #ff5500, #ffff00, #00ffff, #7a00ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 3px;
    text-shadow: 0 0 20px rgba(255, 0, 85, 0.3);
}

.studio-subtitle {
    color: #a0a0d0;
    font-size: 1.2em;
    font-weight: 500;
    margin: 0;
    letter-spacing: 0.8px;
}

/* Status Badge Styles */
.status-badge {
    padding: 16px 20px;
    border-radius: 12px;
    background: #10101c;
    border-left: 6px solid #00ffff;
    color: #ffffff;
    font-weight: 600;
    font-family: 'Consolas', 'Courier New', monospace;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    transition: all 0.3s ease;
}

.status-badge:hover {
    box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
    transform: translateX(4px);
}

/* Diagnostics HTML Styling */
.diag-container {
    background: #0f0f1a;
    border: 1px solid #282845;
    padding: 22px;
    border-radius: 16px;
    color: #e0e0e0;
    font-family: 'Consolas', monospace;
    box-shadow: inset 0 0 15px rgba(0, 0, 0, 0.5);
}

.diag-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
}

.diag-header h4 {
    color: #00ffff;
    margin: 0;
    font-size: 1.2em;
}

.diag-badge {
    background: #00ff66;
    color: #000;
    padding: 4px 10px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 0.8em;
}

.diag-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 15px;
    margin-bottom: 18px;
}

.diag-card {
    background: #161626;
    padding: 14px;
    border-radius: 10px;
    border: 1px solid #2a2a48;
    text-align: center;
    transition: all 0.3s ease;
}

.diag-card:hover {
    border-color: #ff0055;
    box-shadow: 0 0 15px rgba(255, 0, 85, 0.3);
}

.diag-label {
    display: block;
    font-size: 0.85em;
    color: #8a8ab0;
    margin-bottom: 6px;
}

.diag-value {
    display: block;
    font-size: 1.25em;
    font-weight: bold;
    color: #ffffff;
}

.diag-divider {
    border: 0;
    border-top: 1px solid #2a2a45;
    margin: 15px 0;
}

.diag-log-list {
    padding-left: 18px;
    font-size: 0.9em;
    line-height: 1.7;
    margin: 0;
}

/* Footer Styling */
.studio-footer {
    text-align: center;
    padding: 25px;
    color: #8080a8;
    font-size: 0.95em;
    border-top: 1px solid #1a1a30;
    margin-top: 40px;
    letter-spacing: 0.5px;
}

/* Tab Header Backlit Animations */
.tabs > .tab-nav > button {
    background: #10101c !important;
    border: 1px solid #202035 !important;
    color: #8080a8 !important;
    transition: all 0.3s ease !important;
    border-radius: 10px 10px 0 0 !important;
    margin-right: 4px !important;
    padding: 12px 20px !important;
    font-weight: 600 !important;
}

.tabs > .tab-nav > button.selected {
    background: linear-gradient(180deg, #1d1d36, #10101c) !important;
    border-color: #00ffff !important;
    color: #00ffff !important;
    box-shadow: 0 -4px 15px rgba(0, 255, 255, 0.3) !important;
}

.tabs > .tab-nav > button:hover:not(.selected) {
    color: #ffffff !important;
    border-color: #ff0055 !important;
    box-shadow: 0 0 12px rgba(255, 0, 85, 0.3) !important;
}
"""

STUDIO_HEADER_HTML = """
<div class="studio-header">
    <div class="logo-container">
        <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="flameGradMain" x1="0%" y1="100%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#ff0055;stop-opacity:1" />
                    <stop offset="50%" style="stop-color:#7a00ff;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#00ffff;stop-opacity:1" />
                </linearGradient>
                <filter id="glowEffect" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="4" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            <circle cx="50" cy="50" r="46" fill="none" stroke="url(#flameGradMain)" stroke-width="4" stroke-dasharray="10 5" filter="url(#glowEffect)"/>
            <path d="M50 12 C28 35, 18 55, 34 78 C44 90, 56 90, 66 78 C82 55, 72 35, 50 12 Z" fill="url(#flameGradMain)" opacity="0.88"/>
            <path d="M50 28 C36 44, 30 58, 40 72 C46 80, 54 80, 60 72 C70 58, 64 44, 50 28 Z" fill="#08080e"/>
            <path d="M50 44 C42 54, 38 62, 45 70 C48 75, 52 75, 55 70 C62 62, 58 54, 50 44 Z" fill="url(#flameGradMain)"/>
        </svg>
    </div>
    <div class="studio-title">SHADOW FLAMEZ STUDIO</div>
    <div class="studio-subtitle">⚡ Enterprise AI Neural Transparency, FX & Compositing Engine v5.0 Pro</div>
</div>
"""

STUDIO_FOOTER_HTML = """
<div class="studio-footer">
    🔥 <b>Shadow Flamez AI Studio Pro v5.0</b> | Powered by OpenCV, RemBG Neural Models & Accelerated PIL Engine
</div>
"""

# ==============================================================================
# 3. UTILITY & IMAGE CONVERSION ENGINE
# ==============================================================================


class ImageUtils:
    """Provides essential utility functions for fast image conversions and matrix calculations."""

    @staticmethod
    def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
        """Converts PIL Image (RGB/RGBA) to OpenCV NumPy array (BGR/BGRA) efficiently."""
        if pil_image is None:
            raise ValueError("Input PIL Image cannot be None.")

        np_img = np.asarray(pil_image)
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
            new_size = (max(1, int(w * ratio)), max(1, int(h * ratio)))
            return image.resize(new_size, Image.Resampling.LANCZOS)
        return image


# ==============================================================================
# 4. CHECKERBOARD & PATTERN GENERATOR ENGINE
# ==============================================================================


class CheckerboardGenerator:
    """Generates high-performance checkerboard patterns for transparency visualization."""

    @staticmethod
    def create(
        width: int,
        height: int,
        square_size: int = 20,
        color1: Tuple[int, int, int] = (200, 200, 200),
        color2: Tuple[int, int, int] = (240, 240, 240)
    ) -> Image.Image:
        """Creates a high-contrast checkerboard background grid via NumPy vectorization."""
        width = max(1, width)
        height = max(1, height)
        square_size = max(2, square_size)

        # Generate coordinate matrices for fast vectorized checkerboard tiling
        y_coords, x_coords = np.ogrid[:height, :width]
        checker = ((x_coords // square_size) + (y_coords // square_size)) % 2 == 0

        bg = np.zeros((height, width, 4), dtype=np.uint8)
        bg[checker] = [color1[0], color1[1], color1[2], 255]
        bg[~checker] = [color2[0], color2[1], color2[2], 255]

        return Image.fromarray(bg)


# ==============================================================================
# 5. NEURAL AI BACKGROUND REMOVAL ENGINE (REMBG INTEGRATION)
# ==============================================================================


class NeuralEngine:
    """Encapsulates RemBG session models with lazy initialization for fast container boot times."""

    def __init__(self):
        self.sessions: Dict[str, Any] = {}
        # Lazy loading: Do NOT initialize session in __init__ to prevent cloud timeouts during port scanning!

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
        """Performs AI neural background removal with smart threshold fallback."""
        session = self._get_session(model_name)

        output = remove(
            pil_image,
            session=session,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=foreground_threshold,
            alpha_matting_background_threshold=background_threshold
        )
        output_rgba = ImageUtils.ensure_rgba(output)

        # Validate if alpha channel was actually created
        alpha_arr = np.array(output_rgba.split()[3])
        if np.min(alpha_arr) == 255:  # Mask is completely solid / failed
            logger.warning("Neural Engine returned solid mask. Executing adaptive contour fallback...")
            cv_img = ImageUtils.pil_to_cv2(pil_image)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            b, g, r = cv2.split(cv_img)
            rgba_fallback = cv2.merge([b, g, r, mask])
            return ImageUtils.cv2_to_pil(rgba_fallback)

        return output_rgba


# Instantiate global neural engine handler (Lazy loaded)
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

        # Apply Spill Suppression (Remove color cast from subject edges)
        if spill_suppression and screen_type == "Green Screen":
            b_ch, g_ch, r_ch = cv2.split(img_bgr)
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
    def apply_vintage_sepia(pil_image: Image.Image) -> Image.Image:
        """Applies a warm vintage sepia tone filter while preserving alpha."""
        rgba = ImageUtils.ensure_rgba(pil_image)
        np_img = np.array(rgba, dtype=np.float32)

        r, g, b, a = np_img[:, :, 0], np_img[:, :, 1], np_img[:, :, 2], np_img[:, :, 3]

        # Sepia transformation matrix
        new_r = np.clip(0.393 * r + 0.769 * g + 0.189 * b, 0, 255)
        new_g = np.clip(0.349 * r + 0.686 * g + 0.168 * b, 0, 255)
        new_b = np.clip(0.272 * r + 0.534 * g + 0.131 * b, 0, 255)

        sepia_np = np.stack([new_r, new_g, new_b, a], axis=-1).astype(np.uint8)
        return Image.fromarray(sepia_np)

    @staticmethod
    def apply_vignette(pil_image: Image.Image, intensity: float = 0.5) -> Image.Image:
        """Adds a subtle dark vignette overlay onto the composition."""
        rgba = ImageUtils.ensure_rgba(pil_image)
        w, h = rgba.size

        # Build radial gradient mask
        x = np.linspace(-1, 1, w)
        y = np.linspace(-1, 1, h)
        xx, yy = np.meshgrid(x, y)
        radius = np.sqrt(xx**2 + yy**2)

        vignette_mask = np.clip(1.0 - (radius * intensity), 0, 1)

        np_img = np.array(rgba, dtype=np.float32)
        np_img[:, :, 0] *= vignette_mask
        np_img[:, :, 1] *= vignette_mask
        np_img[:, :, 2] *= vignette_mask

        return Image.fromarray(np_img.astype(np.uint8))

    @staticmethod
    def apply_neon_outline(
        pil_image: Image.Image,
        glow_color: str = "#00FFFF",
        thickness: int = 5
    ) -> Image.Image:
        """Generates a glowing backlit neon outline around alpha cutouts OR full photo subjects."""
        rgba = ImageUtils.ensure_rgba(pil_image)
        alpha = rgba.split()[3]
        alpha_np = np.array(alpha)

        # Check if the image has a transparent background or is fully opaque
        if np.max(alpha_np) == np.min(alpha_np):
            # OPAQUE IMAGE FALLBACK: Detect features & subjects via Grayscale Canny
            gray = cv2.cvtColor(np.array(rgba.convert("RGB")), cv2.COLOR_RGB2GRAY)
            gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(gray_blur, 50, 150)
        else:
            # TRANSPARENT CUTOUT: Detect subject perimeter directly from Alpha channel
            edges = cv2.Canny(alpha_np, 100, 200)

        # Expand outline thickness for prominent glow
        if thickness > 1:
            kernel = np.ones((thickness, thickness), np.uint8)
            edges = cv2.dilate(edges, kernel, iterations=1)

        # Gaussian blur for soft aura spread
        edges_blur = cv2.GaussianBlur(edges, (21, 21), 0)

        # Colorize aura layer
        hex_val = glow_color.lstrip('#')
        gr_col = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))

        glow_bg = np.zeros((rgba.height, rgba.width, 4), dtype=np.uint8)
        glow_bg[edges_blur > 5] = [gr_col[0], gr_col[1], gr_col[2], 255]

        # Multi-pass Gaussian blur to create smooth aura diffusion
        glow_pil = Image.fromarray(glow_bg).filter(ImageFilter.GaussianBlur(6))

        # Composite original subject over the newly created glow outline
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
        """Generates smooth multi-color linear gradient backgrounds via NumPy."""
        hex1 = color_start_hex.lstrip('#')
        hex2 = color_end_hex.lstrip('#')

        c1 = np.array([int(hex1[i:i+2], 16) for i in (0, 2, 4)], dtype=float)
        c2 = np.array([int(hex2[i:i+2], 16) for i in (0, 2, 4)], dtype=float)

        bg = np.zeros((height, width, 4), dtype=np.uint8)

        if angle == "Linear Vertical":
            y_ratios = np.linspace(0, 1, height)[:, None]
            col_matrix = (1.0 - y_ratios) * c1 + y_ratios * c2
            bg[:, :, :3] = np.tile(col_matrix[:, None, :], (1, width, 1))

        elif angle == "Linear Horizontal":
            x_ratios = np.linspace(0, 1, width)[None, :]
            col_matrix = (1.0 - x_ratios.T) * c1 + x_ratios.T * c2
            bg[:, :, :3] = np.tile(col_matrix[None, :, :], (height, 1, 1))

        else:  # Linear Diagonal
            y_coords, x_coords = np.ogrid[:height, :width]
            diag_ratios = (x_coords / float(width) + y_coords / float(height)) / 2.0
            bg[:, :, 0] = (1.0 - diag_ratios) * c1[0] + diag_ratios * c2[0]
            bg[:, :, 1] = (1.0 - diag_ratios) * c1[1] + diag_ratios * c2[1]
            bg[:, :, 2] = (1.0 - diag_ratios) * c1[2] + diag_ratios * c2[2]

        bg[:, :, 3] = 255  # Opaque Alpha
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
        """Draws branded text watermark onto image canvas with custom position and opacity."""
        if not text.strip():
            return image

        base = ImageUtils.ensure_rgba(image).copy()
        txt_layer = Image.new("RGBA", base.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        w, h = base.size
        margin = 25

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

        # Draw soft shadow for high text visibility
        shadow_pos = (pos[0] + 2, pos[1] + 2)
        draw.text(shadow_pos, text, font=font, fill=(0, 0, 0, alpha_val // 2))
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
                    elif hasattr(img_data, "name"):  # Gradio NamedString/File object
                        pil_img = Image.open(img_data.name)
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

        # Garbage collect intermediate batch buffers
        gc.collect()

        zip_buffer.seek(0)
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
            f"Image rendered in {elapsed}s | Mode: {processing_mode} | Compositing: {bg_option}",
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
        elif fx_choice == "Vintage Sepia":
            img = ImageEffectsEngine.apply_vintage_sepia(img)
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
    """Constructs the multi-tab Gradio UI Blocks Application with modern backlit FX."""

    with gr.Blocks(
        title="Shadow Flamez AI Studio Pro v5.0",
        css=STUDIO_CSS,
        theme=gr.themes.Slate()
    ) as demo:

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
                                "u2netp",
                                "silueta",
                                "u2net_human_seg"
                            ],
                            value="u2net",
                            label="🧠 AI Neural Model Selection"
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

                # Event Linkage
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
                            choices=["None", "Cyberpunk Teal & Pink", "Vintage Sepia", "Neon Glow Outline"],
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
                btn_refresh_diag = gr.Button("🔄 REFRESH DIAGNOSTICS", variant="secondary")

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
    logger.info("Initializing Shadow Flamez Studio UI Blocks...")
    demo = build_studio_app()
    
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Launching Gradio Server on 0.0.0.0:{port}...")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        show_error=True
    )
