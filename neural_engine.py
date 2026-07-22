"""
neural_engine.py - Background Removal Engine using rembg
"""
from typing import Optional
from PIL import Image

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

neural_engine = NeuralEngine()
