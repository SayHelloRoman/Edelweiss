import glfw
from OpenGL.GL import *

from .audio import SoundManager
from .figure import Square, Circle, GameObject
from .utils import load_icon, GLFWimage
import numpy as np
import abc
from PIL import Image as PILImage

class GameEngine:
    def __init__(self, width=800, height=600, title="Game Engine"):
        self.width = width
        self.height = height
        self.title = title
        self.window = None
        self.scene = None
        self.running = False

    def initialize(self):
        if not glfw.init():
            raise Exception("Failed to initialize GLFW")
        
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 5)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)

        self.window = glfw.create_window(self.width, self.height, self.title, None, None)
        if not self.window:
            glfw.terminate()
            raise Exception("Failed to create window")
        
        icon_img = PILImage.open("edelweiss/edelweiss.png").convert("RGBA").resize((64, 64), PILImage.ANTIALIAS)
        icon_data = icon_img.tobytes()
        width, height = icon_img.size
        pixels = list(icon_img.getdata())
        pixel_rows = [pixels[i * width:(i + 1) * width] for i in range(height)]


        glfw.set_window_icon(self.window, 1, [(width, height, pixel_rows)])
        
        glfw.make_context_current(self.window)
        print(f"OpenGL Version: {glGetString(GL_VERSION).decode('utf-8')}")

        # Устанавливаем обработчик для события закрытия окна
        glfw.set_window_close_callback(self.window, self.on_window_close)

    def set_scene(self, scene):
        if not isinstance(scene, Scene):
            raise ValueError("Scene must be an instance of Scene class")
        if not self.window:
            self.initialize()
        self.scene = scene
        for obj in self.scene.objects.values():
            obj.initialize()

    def run(self):
        if not self.window:
            self.initialize()
        if not self.scene:
            raise Exception("Scene is not set")
        
        self.running = True
        while self.running and not glfw.window_should_close(self.window):
            self.scene.update()
            self.scene.render()
            glfw.swap_buffers(self.window)
            glfw.poll_events()
        
        self.cleanup()

    def cleanup(self):
        if self.scene:
            self.scene.cleanup()
        glfw.terminate()

    def stop(self):
        self.running = False

    def on_window_close(self, *args, **kwargs):
        SoundManager().stop()
        print(SoundManager().run)
        SoundManager().close()


class Scene(abc.ABC):
    def __init__(self):
        self.objects = {}  # Hash table for objects

    def add_object(self, obj):
        if not isinstance(obj, GameObject):
            raise ValueError("Object must be an instance of GameObject")
        if obj.name in self.objects:
            raise ValueError(f"Object with name '{obj.name}' already exists")
        self.objects[obj.name] = obj

    @abc.abstractmethod
    def update(self):
        """Update scene logic - overridden in subclass"""
        pass

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glClearColor(0.1, 0.1, 0.1, 1.0)
        for obj in self.objects.values():
            obj.render()

    def cleanup(self):
        for obj in self.objects.values():
            obj.cleanup()


class MyScene(Scene):
    def __init__(self):
        super().__init__()
        self.time = 0.0  # For animation

    def update(self):
        self.time += 0.016  # Approximately 60 FPS
        # Example logic: move objects based on their names
        if "square1" in self.objects:
            self.objects["square1"].set_position(np.sin(self.time) * 0.5, 0.0)
        if "circle1" in self.objects:
            self.objects["circle1"].set_position(-np.sin(self.time) * 0.5, 0.0)
        if "square2" in self.objects:
            self.objects["square2"].set_position(0.0, np.cos(self.time) * 0.5)


if __name__ == "__main__":
    engine = GameEngine(800, 600, "Test with names")
    scene = MyScene()
    
    # Adding objects with explicit names
    scene.add_object(Square(name="square1"))
    scene.add_object(Circle(name="circle1"))
    scene.add_object(Square(name="square2"))
    
    engine.set_scene(scene)
    engine.run()