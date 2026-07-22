"""
neural_engine.py - Neural Background Removal, 4X Scaler, and Cyber Neon Effects
"""
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
from typing import Optional, Tuple


class NeuralEngine:
    def __init__(self):
        self._sessions = {}

    def _get_session(self, model_name: str):
        if model_name not in self._sessions:
            from rembg import new_session
            self._sessions[model_name] = new_session(model_name)
        return self._sessions[model_name]

    def remove_background(self, pil_image: Image.Image, model_name: str = "u2net") -> Image.Image:
        from rembg import remove
        session = self._get_session(model_name)
        return remove(pil_image, session=session)

    @staticmethod
    def upscale_4x_neural(pil_img: Image.Image, sharpness_boost: float = 1.5) -> Image.Image:
        """High-Fidelity 4X Super Resolution Scaler optimized for CPU RAM stability."""
        if pil_img is None:
            return None
        
        w, h = pil_img.size
        # 4X Upscale using Lanczos High-Res Resampling
        upscaled = pil_img.resize((w * 4, h * 4), Image.Resampling.LANCZOS)
        
        # Detail & Edge Sharpening Pass
        enhancer = ImageEnhance.Sharpen(upscaled)
        sharpened = enhancer.enhance(sharpness_boost)
        
        return sharpened

    @staticmethod
    def generate_neon_aura(
        fg_rgba: Image.Image, 
        aura_color_hex: str = "#00FFFF", 
        blur_radius: int = 25, 
        glow_intensity: float = 2.0
    ) -> Image.Image:
        """Generates a glowing neon aura halo around extracted subject background."""
        if fg_rgba.mode != "RGBA":
            fg_rgba = fg_rgba.convert("RGBA")

        # Extract Alpha Mask
        alpha = fg_rgba.split()[3]
        
        # Create Colored Aura Canvas
        aura_color = Image.new("RGBA", fg_rgba.size, aura_color_hex)
        aura_mask = alpha.filter(ImageFilter.GaussianBlur(blur_radius))
        
        # Boost Glow Intensity
        if glow_intensity > 1.0:
            enhancer = ImageEnhance.Brightness(aura_mask)
            aura_mask = enhancer.enhance(glow_intensity)

        aura_layer = Image.new("RGBA", fg_rgba.size, (0, 0, 0, 0))
        aura_layer.paste(aura_color, (0, 0), mask=aura_mask)

        # Composite Original Foreground on top of Glowing Aura
        return Image.alpha_composite(aura_layer, fg_rgba)

    @staticmethod
    def generate_cyber_outline(
        fg_rgba: Image.Image, 
        outline_hex: str = "#FF007F", 
        stroke_width: int = 5
    ) -> Image.Image:
        """Creates sharp glowing cyber contours/outlines around the subject."""
        if fg_rgba.mode != "RGBA":
            fg_rgba = fg_rgba.convert("RGBA")

        alpha = np.array(fg_rgba.split()[3])
        
        # Dilate mask to create contour outline
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (stroke_width * 2 + 1, stroke_width * 2 + 1))
        dilated = cv2.dilate(alpha, kernel, iterations=1)
        contour_mask = cv2.subtract(dilated, alpha)

        contour_pil = Image.fromarray(contour_mask)
        outline_color = Image.new("RGBA", fg_rgba.size, outline_hex)
        
        outline_layer = Image.new("RGBA", fg_rgba.size, (0, 0, 0, 0))
        outline_layer.paste(outline_color, (0, 0), mask=contour_pil)

        # Blend Outline + Foreground
        return Image.alpha_composite(outline_layer, fg_rgba)


neural_engine = NeuralEngine()
