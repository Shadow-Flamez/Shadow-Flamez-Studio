"""
chroma_engine.py - Color Keying Engine (Green/Blue Screen)
"""
import cv2
import numpy as np
from PIL import Image
from utils import ImageUtils

class ChromaKeyEngine:
    @staticmethod
    def process_keying(pil_image: Image.Image, screen_type: str = "Green Screen") -> Image.Image:
        cv_img = ImageUtils.pil_to_cv2(pil_image)
        hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)

        if "Green" in screen_type:
            lower_bound = np.array([35, 40, 40])
            upper_bound = np.array([85, 255, 255])
        else:
            lower_bound = np.array([100, 50, 50])
            upper_bound = np.array([140, 255, 255])

        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        inv_mask = cv2.bitwise_not(mask)

        b, g, r = cv2.split(cv_img[:, :, :3])
        rgba = cv2.merge([b, g, r, inv_mask])
        return ImageUtils.cv2_to_pil(rgba)
