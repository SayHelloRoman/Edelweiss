from edelweiss import GameEngine, Scene, Square
from edelweiss.audio import SoundManager
from edelweiss.widgets import Button
import glfw
import numpy as np
import random

class MyScene(Scene):
    def __init__(self):
        super().__init__()
        self.time = 0.0

        button = Button(
            "test_button",
            400, 300, 200, 100,
            [0.5, 0.0, 0.0],
            outline_color=[1, 1, 1],
            outline_width=3.0,
            radius=0.4,
            on_click=lambda x: x.set_position(random.randint(1, 500), random.randint(1, 500))
        )

        self.window = glfw.get_current_context()
    
        self.add_object(button)

    def update(self):
        self.time += 0.016

if __name__ == "__main__":
    sound_manager = SoundManager()
    engine = GameEngine(800, 600, "Bouncing Square")
    scene = MyScene()
    engine.set_scene(scene)
    engine.run()