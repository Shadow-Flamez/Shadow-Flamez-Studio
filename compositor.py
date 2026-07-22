"""
compositor.py - Layer Compositing Engine
"""
from PIL import Image, ImageColor

class CompositingEngine:
    @staticmethod
    def composite_layers(foreground: Image.Image, bg_option: str, solid_hex: str = "#000000") -> Image.Image:
        if foreground.mode != "RGBA":
            foreground = foreground.convert("RGBA")

        if bg_option == "Transparent (PNG)" or bg_option == "Checkerboard Preview":
            return foreground

        bg_color = ImageColor.getcolor(solid_hex, "RGBA")
        background = Image.new("RGBA", foreground.size, bg_color)
        return Image.alpha_composite(background, foreground)
