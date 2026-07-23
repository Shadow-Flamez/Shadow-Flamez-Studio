"""
neural_engine.py - Advanced AI Processing, Filters, Relighting, Shadows & FX
"""
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageColor
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

    # --- FEATURE 1: 4X Neural Super Resolution ---
    @staticmethod
    def upscale_4x_neural(pil_img: Image.Image, sharpness_boost: float = 1.5) -> Image.Image:
        if pil_img is None:
            return None
        w, h = pil_img.size
        upscaled = pil_img.resize((w * 4, h * 4), Image.Resampling.LANCZOS)
        enhancer = ImageEnhance.Sharpen(upscaled)
        return enhancer.enhance(sharpness_boost)

    # --- FEATURE 2: Neon Aura Glow Halo ---
    @staticmethod
    def generate_neon_aura(fg_rgba: Image.Image, aura_color_hex: str = "#00FFFF", blur_radius: int = 25, glow_intensity: float = 2.0) -> Image.Image:
        if fg_rgba.mode != "RGBA":
            fg_rgba = fg_rgba.convert("RGBA")
        alpha = fg_rgba.split()[3]
        aura_color = Image.new("RGBA", fg_rgba.size, aura_color_hex)
        aura_mask = alpha.filter(ImageFilter.GaussianBlur(blur_radius))
        if glow_intensity > 1.0:
            aura_mask = ImageEnhance.Brightness(aura_mask).enhance(glow_intensity)
        aura_layer = Image.new("RGBA", fg_rgba.size, (0, 0, 0, 0))
        aura_layer.paste(aura_color, (0, 0), mask=aura_mask)
        return Image.alpha_composite(aura_layer, fg_rgba)

    # --- FEATURE 3: Cyber Outline Contours ---
    @staticmethod
    def generate_cyber_outline(fg_rgba: Image.Image, outline_hex: str = "#FF007F", stroke_width: int = 5) -> Image.Image:
        if fg_rgba.mode != "RGBA":
            fg_rgba = fg_rgba.convert("RGBA")
        alpha = np.array(fg_rgba.split()[3])
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (stroke_width * 2 + 1, stroke_width * 2 + 1))
        dilated = cv2.dilate(alpha, kernel, iterations=1)
        contour_mask = cv2.subtract(dilated, alpha)
        outline_color = Image.new("RGBA", fg_rgba.size, outline_hex)
        outline_layer = Image.new("RGBA", fg_rgba.size, (0, 0, 0, 0))
        outline_layer.paste(outline_color, (0, 0), mask=Image.fromarray(contour_mask))
        return Image.alpha_composite(outline_layer, fg_rgba)

    # --- FEATURE 4: Dynamic Realistic Drop Shadows ---
    @staticmethod
    def apply_drop_shadow(fg_rgba: Image.Image, offset_x: int = 15, offset_y: int = 20, blur_r: int = 15, shadow_hex: str = "#000000", opacity: float = 0.6) -> Image.Image:
        if fg_rgba.mode != "RGBA":
            fg_rgba = fg_rgba.convert("RGBA")
        alpha = fg_rgba.split()[3]
        shadow_mask = alpha.filter(ImageFilter.GaussianBlur(blur_r))
        shadow_mask = ImageEnhance.Brightness(shadow_mask).enhance(opacity)
        
        shadow_img = Image.new("RGBA", fg_rgba.size, shadow_hex)
        shadow_canvas = Image.new("RGBA", fg_rgba.size, (0, 0, 0, 0))
        shadow_canvas.paste(shadow_img, (offset_x, offset_y), mask=shadow_mask)
        return Image.alpha_composite(shadow_canvas, fg_rgba)

    # --- FEATURE 5: Realistic Bokeh Blur Background Simulator ---
    @staticmethod
    def simulate_bokeh_bg(fg_rgba: Image.Image, bg_img: Image.Image, blur_amount: int = 20) -> Image.Image:
        if fg_rgba.mode != "RGBA":
            fg_rgba = fg_rgba.convert("RGBA")
        bg_resized = bg_img.resize(fg_rgba.size, Image.Resampling.LANCZOS)
        blurred_bg = bg_resized.filter(ImageFilter.GaussianBlur(blur_amount))
        return Image.alpha_composite(blurred_bg.convert("RGBA"), fg_rgba)

    # --- FEATURE 6: Cyberpunk RGB Glitch Split ---
    @staticmethod
    def apply_rgb_glitch(pil_img: Image.Image, offset: int = 10) -> Image.Image:
        img_np = np.array(pil_img)
        if len(img_np.shape) < 3:
            return pil_img
        r = np.roll(img_np[:, :, 0], offset, axis=1)
        g = img_np[:, :, 1]
        b = np.roll(img_np[:, :, 2], -offset, axis=1)
        glitched = np.stack([r, g, b], axis=2)
        if img_np.shape[2] == 4:
            glitched = np.dstack([glitched, img_np[:, :, 3]])
        return Image.fromarray(glitched)

    # --- FEATURE 7: Auto Magic Color & Tone Enhancer ---
    @staticmethod
    def auto_enhance_tone(pil_img: Image.Image, contrast: float = 1.2, brightness: float = 1.1, color: float = 1.25) -> Image.Image:
        img = ImageEnhance.Contrast(pil_img).enhance(contrast)
        img = ImageEnhance.Brightness(img).enhance(brightness)
        return ImageEnhance.Color(img).enhance(color)

    # --- FEATURE 8: Cinematic LUT Color Grading ---
    @staticmethod
    def apply_lut_preset(pil_img: Image.Image, preset: str = "Cyberpunk Neo") -> Image.Image:
        img = pil_img.convert("RGB")
        img_np = np.array(img).astype(float) / 255.0

        if preset == "Cyberpunk Neo":
            img_np[:, :, 0] = np.clip(img_np[:, :, 0] * 1.2, 0, 1) # Red boost
            img_np[:, :, 2] = np.clip(img_np[:, :, 2] * 1.4, 0, 1) # Blue boost
        elif preset == "Matrix Green":
            img_np[:, :, 0] *= 0.3
            img_np[:, :, 1] = np.clip(img_np[:, :, 1] * 1.4, 0, 1)
            img_np[:, :, 2] *= 0.3
        elif preset == "Golden Hour":
            img_np[:, :, 0] = np.clip(img_np[:, :, 0] * 1.3, 0, 1)
            img_np[:, :, 1] = np.clip(img_np[:, :, 1] * 1.1, 0, 1)
            img_np[:, :, 2] *= 0.6
        elif preset == "Noir Monochrome":
            gray = np.dot(img_np[..., :3], [0.2989, 0.5870, 0.1140])
            img_np = np.stack([gray, gray, gray], axis=-1)

        result = (img_np * 255).astype(np.uint8)
        res_pil = Image.fromarray(result)
        if pil_img.mode == "RGBA":
            res_pil = res_pil.convert("RGBA")
            res_pil.putalpha(pil_img.split()[3])
        return res_pil

    # --- FEATURE 9: Selective Color Isolation / Color Splash ---
    @staticmethod
    def color_splash(pil_img: Image.Image, keep_color: str = "Red") -> Image.Image:
        cv_img = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)

        if keep_color == "Red":
            mask1 = cv2.inRange(hsv, np.array([0, 70, 50]), np.array([10, 255, 255]))
            mask2 = cv2.inRange(hsv, np.array([170, 70, 50]), np.array([180, 255, 255]))
            mask = mask1 | mask2
        elif keep_color == "Green":
            mask = cv2.inRange(hsv, np.array([36, 50, 50]), np.array([86, 255, 255]))
        else: # Blue
            mask = cv2.inRange(hsv, np.array([94, 80, 2] ), np.array([126, 255, 255]))

        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        gray_3ch = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        splash = np.where(mask[:, :, None] == 255, cv_img, gray_3ch)
        
        res_pil = Image.fromarray(cv2.cvtColor(splash, cv2.COLOR_BGR2RGB))
        if pil_img.mode == "RGBA":
            res_pil = res_pil.convert("RGBA")
            res_pil.putalpha(pil_img.split()[3])
        return res_pil

    # --- FEATURE 10: Retro 8-Bit Pixel Art Downscaler ---
    @staticmethod
    def pixel_art_downscale(pil_img: Image.Image, pixel_size: int = 12) -> Image.Image:
        w, h = pil_img.size
        small = pil_img.resize((max(1, w // pixel_size), max(1, h // pixel_size)), Image.Resampling.NEAREST)
        return small.resize((w, h), Image.Resampling.NEAREST)


neural_engine = NeuralEngine()
