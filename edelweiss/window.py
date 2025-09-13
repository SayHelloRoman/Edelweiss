import sys
import glfw
from OpenGL.GL import *
import numpy as np
import abc
from PIL import Image as PILImage

# Assuming these modules exist; not present in the minimal example
from edelweiss.widgets.button import Button  # Use the correct import path for Button
from edelweiss.figure import Square, Circle, GameObject  # Expected imports


def setup_projection(width, height):
    """Orthographic projection setup for a fixed-size window."""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, width, height, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)


class GameEngine:
    def __init__(self, width=800, height=600, title="Game Engine"):
        self.width = width
        self.height = height
        self.title = title
        self.window = None
        self.scene = None
        self.running = False
        self.key_states = {}
        self.mouse_button_states = {}
        self.xpos = 0
        self.ypos = 0

        if not glfw.init():
            raise Exception("Failed to initialize GLFW")

        # IMPORTANT: set window hints BEFORE creating the window.
        # Keep default context (on macOS it's often GL 2.1) to preserve compatibility.
        glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)  # Make the window non-resizable

        self.window = glfw.create_window(
            self.width, self.height, self.title, None, None
        )
        if not self.window:
            glfw.terminate()
            raise Exception("Failed to create window")

        glfw.make_context_current(self.window)
        glfw.swap_interval(1)  # Enable vsync
        setup_projection(width, height)

    def initialize(self):
        """Initialization after the window is created and the context is current."""
        # Do not set a window icon on macOS (Cocoa warning). Other platforms are fine.
        if sys.platform != "darwin":
            try:
                icon_img = (
                    PILImage.open("edelweiss/edelweiss.png")
                    .convert("RGBA")
                    .resize((64, 64))
                )
                width, height = icon_img.size
                pixels = list(icon_img.getdata())
                pixel_rows = [
                    pixels[i * width : (i + 1) * width] for i in range(height)
                ]
                glfw.set_window_icon(self.window, 1, [(width, height, pixel_rows)])
            except Exception:
                # Icon is non-critical; if the file is missing/invalid — just skip.
                pass

        # Print OpenGL version (useful for diagnostics)
        print(f"OpenGL Version: {glGetString(GL_VERSION).decode('utf-8')}")

        # Register input/system callbacks
        glfw.set_key_callback(self.window, self.key_callback)
        glfw.set_cursor_pos_callback(self.window, self.cursor_pos_callback)
        glfw.set_window_close_callback(self.window, self.on_window_close)
        glfw.set_mouse_button_callback(self.window, self.mouse_button_callback)
        glfw.set_window_size_callback(self.window, self.window_resize_callback)

        # Basic check: shader functions are available only when the context is current
        if not glCreateShader:
            raise Exception(
                "glCreateShader is not loaded! Ensure the OpenGL context is current."
            )

    def window_resize_callback(self, window, width, height):
        """Resize callback. Window is fixed-size, but keep this for DPI changes, etc."""
        glViewport(0, 0, width, height)
        setup_projection(width, height)

    def key_callback(self, window, key, scancode, action, mods):
        """Track key presses (True/False state)."""
        if action == glfw.PRESS:
            self.key_states[key] = True
        elif action == glfw.RELEASE:
            self.key_states[key] = False

    def mouse_button_callback(self, window, button, action, mods):
        """Track mouse clicks and forward the event to the scene."""
        if action == glfw.PRESS:
            self.mouse_button_states[button] = True
        elif action == glfw.RELEASE:
            self.mouse_button_states[button] = False
        if self.scene:
            self.scene.handle_mouse_button(button, action, mods)

    def cursor_pos_callback(self, window, xpos, ypos):
        """Track cursor position and forward the event to the scene."""
        self.xpos = xpos
        self.ypos = ypos
        if self.scene:
            self.scene.handle_cursor_pos(xpos, ypos)

    def set_scene(self, scene):
        """Attach a scene, wire up window/input, and call initialize() on its objects."""
        if not isinstance(scene, Scene):
            raise ValueError("Scene must be an instance of Scene class")
        if not self.window:
            self.initialize()
        self.scene = scene
        self.scene.key_states = self.key_states
        self.scene.mouse_button_states = self.mouse_button_states
        self.scene.window = self.window
        self.scene.engine = self  # Give the scene a reference to the engine
        for obj in self.scene.objects.values():
            if "initialize" in dir(obj):
                obj.initialize()

    def run(self):
        """Main render loop."""
        self.initialize()
        self.running = True
        while self.running and not glfw.window_should_close(self.window):
            self.scene.update()
            self.scene.render()
            glfw.swap_buffers(self.window)
            glfw.poll_events()
        self.cleanup()

    def cleanup(self):
        """Release resources on shutdown."""
        if self.scene:
            self.scene.cleanup()
        glfw.terminate()

    def stop(self):
        """Gracefully stop the main loop."""
        self.running = False

    def on_window_close(self, *args, **kwargs):
        """Handle user-initiated window close."""
        self.stop()


class Scene(abc.ABC):
    def __init__(self):
        self.objects = {}
        self.window = None
        self.key_states = {}
        self.mouse_button_states = {}
        self.engine = None  # Reference to GameEngine

    def add_object(self, obj):
        """Add an object to the scene by a unique name."""
        if obj.name in self.objects:
            raise ValueError(f"Object with name '{obj.name}' already exists")
        self.objects[obj.name] = obj

    @abc.abstractmethod
    def update(self):
        """Scene logic / objects update step."""
        pass

    def render(self):
        """Render the scene: clear the buffer and draw all objects."""
        glClear(GL_COLOR_BUFFER_BIT)
        glClearColor(0.1, 0.1, 0.1, 1.0)
        for obj in self.objects.values():
            obj.render()

    def handle_cursor_pos(self, xpos, ypos):
        """Forward cursor movement to objects that handle it."""
        for obj in self.objects.values():
            if hasattr(obj, "handle_cursor_pos"):
                obj.handle_cursor_pos(xpos, ypos)

    def handle_mouse_button(self, button, action, mods):
        """Forward mouse button events to objects that handle them."""
        for obj in self.objects.values():
            if hasattr(obj, "handle_mouse_button"):
                obj.handle_mouse_button(button, action, mods)

    def cleanup(self):
        """Clean up object resources on exit."""
        for obj in self.objects.values():
            obj.cleanup()


# Test scene (same as in the original example).
class MyScene(Scene):
    def __init__(self):
        super().__init__()
        self.time = 0.0

        # Button callbacks
        def on_hover(button):
            button.color = np.array([1.0, 0.5, 0.5], dtype=np.float32)  # Light red

        def on_press(button):
            button.color = np.array([0.5, 0.0, 0.0], dtype=np.float32)  # Dark red

        button = Button(
            "test_button",
            400,
            300,
            200,
            100,
            [1.0, 0.0, 0.0],
            on_hover=on_hover,
            on_press=on_press,
            on_click=lambda x: print(100),
            outline_color=[0.0, 0.0, 0.0],
            outline_width=5.0,
            radius=0.4,
        )

        self.add_object(button)

    def update(self):
        self.time += 0.016
        # Update coordinates of other objects if present
        if "square1" in self.objects:
            self.objects["square1"].set_position(np.sin(self.time) * 0.5, 0.0)
        if "circle1" in self.objects:
            self.objects["circle1"].set_position(-np.sin(self.time) * 0.5, 0.0)
        if "square2" in self.objects:
            self.objects["square2"].set_position(0.0, np.cos(self.time) * 0.5)


if __name__ == "__main__":
    engine = GameEngine(800, 600, "Test with Button")
    scene = MyScene()

    # Add additional test objects (if needed)
    scene.add_object(Square(name="square1"))
    scene.add_object(Circle(name="circle1"))
    scene.add_object(Square(name="square2"))

    engine.set_scene(scene)
    engine.run()
