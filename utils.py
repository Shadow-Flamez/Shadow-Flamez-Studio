"""
utils.py - Core Utilities for Image Processing
"""
import io
import cv2
import numpy as np
from PIL import Image

class ImageUtils:
    @staticmethod
    def pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
        """Convert a PIL Image (RGB/RGBA) to OpenCV BGR/BGRA format."""
        if pil_img is None:
            raise ValueError("Input PIL image cannot be None")
        
        # Ensure image is in RGB or RGBA mode
        if pil_img.mode not in ("RGB", "RGBA"):
            pil_img = pil_img.convert("RGBA" if "A" in pil_img.mode else "RGB")
            
        numpy_img = np.array(pil_img)
        if pil_img.mode == "RGBA":
            return cv2.cvtColor(numpy_img, cv2.COLOR_RGBA2BGRA)
        else:
            return cv2.cvtColor(numpy_img, cv2.COLOR_RGB2BGR)

    @staticmethod
    def cv2_to_pil(cv2_img: np.ndarray) -> Image.Image:
        """Convert an OpenCV image (BGR/BGRA) to a PIL Image (RGB/RGBA)."""
        if cv2_img is None:
            raise ValueError("Input CV2 image matrix cannot be None")
            
        if len(cv2_img.shape) == 3 and cv2_img.shape[2] == 4:
            rgb_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGRA2RGBA)
            return Image.fromarray(rgb_img, mode="RGBA")
        elif len(cv2_img.shape) == 3 and cv2_img.shape[2] == 3:
            rgb_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb_img, mode="RGB")
        else:
            return Image.fromarray(cv2_img)

    @staticmethod
    def ensure_rgba(pil_img: Image.Image) -> Image.Image:
        """Ensure PIL image has an Alpha transparency channel."""
        if pil_img is None:
            raise ValueError("Input image cannot be None")
        return pil_img.convert("RGBA") if pil_img.mode != "RGBA" else pil_img

    @staticmethod
    def resize_for_performance(pil_img: Image.Image, max_dim: int = 1920) -> Image.Image:
        """Resize large images down to prevent OOM errors on free tier hosting."""
        if pil_img is None:
            return None
            
        w, h = pil_img.size
        if max(w, h) <= max_dim:
            return pil_img
            
        scale = max_dim / float(max(w, h))
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        return pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
