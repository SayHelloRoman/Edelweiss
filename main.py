from edelweiss import GameEngine, Scene, Square
import glfw
import numpy as np

class MyScene(Scene):
    def __init__(self):
        super().__init__()
        self.last_time = 0.0

    def update(self):
        current_time = glfw.get_time()
        delta_time = current_time - self.last_time if self.last_time != 0.0 else 0.0
        self.last_time = current_time
        
        if "square1" in self.objects:
            obj = self.objects["square1"]
            half_size = 0.5 * obj.scale  # Половина размера квадрата
            
            # Обновляем позицию по X и Y
            obj.position += obj.velocity * delta_time
            
            # Проверяем столкновение с границами и меняем направление
            if obj.position[1] > 1 - half_size or obj.position[1] < -1 + half_size:
                obj.velocity[1] = -obj.velocity[1]
            if obj.position[0] > 1 - half_size or obj.position[0] < -1 + half_size:
                obj.velocity[0] = -obj.velocity[0]

if __name__ == "__main__":
    engine = GameEngine(800, 600, "Bouncing Square")
    scene = MyScene()

    x = Square(name='square1')
    x.set_position(0.0, 0.0)
    x.set_scale(0.2)
    x.velocity = np.array([0.7, 1.0, 0.0], dtype=np.float32)  # Скорость по X и Y

    scene.add_object(x)
    engine.set_scene(scene)
    engine.run()