from edelweiss import GameEngine, Scene, Square, Circle
import time
import numpy as np

class MyScene(Scene):
    def __init__(self):
        super().__init__()
        self.time = 0.0

    def update(self):
        self.time += 0.010
        if "square1" in self.objects:
            self.objects["square1"].set_position(np.sin(self.time) * 0.5, 0.0)


if __name__ == "__main__":
    engine = GameEngine(800, 600, "edelweiss test")
    scene = MyScene()

    x = Square(name='square1')
    x.set_position(-0.5, 0.0)
    

    scene.add_object(x)

    engine.set_scene(scene)
    engine.run()