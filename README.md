<div style="text-align: center;">
  <p><img src="https://github.com/SayHelloRoman/Edelweiss/blob/main/image/edelweiss.png" alt="Edelweiss Logo" style="display: block; margin: 0 auto;"></p>
  <h1>Edelweiss</h1>
  <p>Edelweiss is a lightweight game engine framework built with Python and OpenGL, designed to simplify the creation of 2D games</p>
  <p style="font-weight:bold;">Note: This project is currently in beta testing. Features may change, and there may be bugs. Contributions and feedback are welcome!</p>
</div>

## Features

- Modular structure with separate classes for the game engine, scenes, and game objects.
- Support for basic shapes like squares and circles with customizable properties (position, color, scale).
- Scene management system for easy addition and manipulation of game objects.
- Basic animation and movement logic for objects.

## Technologies Used

- Python 3.x
- PyOpenGL
- GLFW
- NumPy

## Usage

This will launch a window displaying animated squares.

<div style="text-align: center;">
  <img src="https://github.com/SayHelloRoman/Edelweiss/blob/main/image/example.gif" alt="GIF">
</div>  

```python
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
    x.set
    

    scene.add_object(x)

    engine.set_scene(scene)
    engine.run()
```

## Installation

1. Clone the repository:

```git clone https://github.com/yourusername/edelweiss.git
cd edelweiss
```

2. Install the required Python packages:
```
pip install PyOpenGL PyOpenGL_accelerate glfw numpy
```

3. Ensure you have a compatible version of OpenGL installed on your system.