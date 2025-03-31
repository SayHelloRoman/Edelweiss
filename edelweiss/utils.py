import glfw
from OpenGL.GL import *
import numpy as np
from PIL import Image as PILImage
import ctypes


class GLFWimage(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("pixels", ctypes.POINTER(ctypes.c_ubyte))
    ]

def load_icon(filename):
    pil_img = PILImage.open(filename).convert('RGBA')
    width, height = pil_img.size
    img_data = np.array(pil_img, dtype=np.uint8)
    data = img_data.flatten()
    c_data = (ctypes.c_ubyte * len(data))(*data)
    image = GLFWimage(width, height, c_data)
    return image