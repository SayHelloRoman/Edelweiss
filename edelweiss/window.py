import sys
import glfw
from OpenGL.GL import *
import numpy as np
import abc
from PIL import Image as PILImage

# Предполагаю, что у тебя есть эти модули, но их нет в примере
from edelweiss.widgets.button import Button  # Подставь правильный путь к Button
from edelweiss.figure import Square, Circle, GameObject  # Предполагаемые импорты


def setup_projection(width, height):
    """Настройка ортографической проекции под фиксированное окно."""
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

        # ВАЖНО: хинты нужно ставить ДО создания окна
        # Оставляем дефолтный контекст (на macOS это часто GL 2.1), чтобы не ломать совместимость.
        glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)  # Делаем окно нересайзабельным

        self.window = glfw.create_window(
            self.width, self.height, self.title, None, None
        )
        if not self.window:
            glfw.terminate()
            raise Exception("Failed to create window")

        glfw.make_context_current(self.window)
        glfw.swap_interval(1)  # Включаем vsync
        setup_projection(width, height)

    def initialize(self):
        """Инициализация после создания окна и активации контекста."""
        # Иконку окна на macOS не устанавливаем (предупреждение от Cocoa), на других платформах — можно.
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
                # Иконка — не критично; если файл не найден/формат не подошёл — просто пропускаем.
                pass

        # Печатаем версию OpenGL (полезно для диагностики)
        print(f"OpenGL Version: {glGetString(GL_VERSION).decode('utf-8')}")

        # Колбэки ввода/системных событий
        glfw.set_key_callback(self.window, self.key_callback)
        glfw.set_cursor_pos_callback(self.window, self.cursor_pos_callback)
        glfw.set_window_close_callback(self.window, self.on_window_close)
        glfw.set_mouse_button_callback(self.window, self.mouse_button_callback)
        glfw.set_window_size_callback(self.window, self.window_resize_callback)

        # Базовая проверка: функции шейдеров доступны только при активном контексте
        if not glCreateShader:
            raise Exception(
                "glCreateShader не загружен! Проверь, что контекст OpenGL активен."
            )

    def window_resize_callback(self, window, width, height):
        """Колбэк ресайза. Окно у нас фиксированное, но оставляем на случай смены DPI и т.п."""
        glViewport(0, 0, width, height)
        setup_projection(width, height)

    def key_callback(self, window, key, scancode, action, mods):
        """Отслеживание нажатий клавиш (состояние True/False)."""
        if action == glfw.PRESS:
            self.key_states[key] = True
        elif action == glfw.RELEASE:
            self.key_states[key] = False

    def mouse_button_callback(self, window, button, action, mods):
        """Отслеживание нажатий мыши и прокидывание события в сцену."""
        if action == glfw.PRESS:
            self.mouse_button_states[button] = True
        elif action == glfw.RELEASE:
            self.mouse_button_states[button] = False
        if self.scene:
            self.scene.handle_mouse_button(button, action, mods)

    def cursor_pos_callback(self, window, xpos, ypos):
        """Отслеживание позиции курсора и прокидывание события в сцену."""
        self.xpos = xpos
        self.ypos = ypos
        if self.scene:
            self.scene.handle_cursor_pos(xpos, ypos)

    def set_scene(self, scene):
        """Назначаем сцену, прокидываем ей доступ к окну/вводу и вызываем initialize() у объектов."""
        if not isinstance(scene, Scene):
            raise ValueError("Scene must be an instance of Scene class")
        if not self.window:
            self.initialize()
        self.scene = scene
        self.scene.key_states = self.key_states
        self.scene.mouse_button_states = self.mouse_button_states
        self.scene.window = self.window
        self.scene.engine = self  # Даем сцене ссылку на движок
        for obj in self.scene.objects.values():
            if "initialize" in dir(obj):
                obj.initialize()

    def run(self):
        """Главный цикл рендера."""
        self.initialize()
        self.running = True
        while self.running and not glfw.window_should_close(self.window):
            self.scene.update()
            self.scene.render()
            glfw.swap_buffers(self.window)
            glfw.poll_events()
        self.cleanup()

    def cleanup(self):
        """Очистка ресурсов при завершении."""
        if self.scene:
            self.scene.cleanup()
        glfw.terminate()

    def stop(self):
        """Мягкая остановка главного цикла."""
        self.running = False

    def on_window_close(self, *args, **kwargs):
        """Закрытие окна пользователем."""
        self.stop()


class Scene(abc.ABC):
    def __init__(self):
        self.objects = {}
        self.window = None
        self.key_states = {}
        self.mouse_button_states = {}
        self.engine = None  # Ссылка на GameEngine

    def add_object(self, obj):
        """Добавление объекта в сцену по уникальному имени."""
        if obj.name in self.objects:
            raise ValueError(f"Object with name '{obj.name}' already exists")
        self.objects[obj.name] = obj

    @abc.abstractmethod
    def update(self):
        """Логика сцены / обновление состояния объектов."""
        pass

    def render(self):
        """Отрисовка сцены: чистим буфер и рендерим все объекты."""
        glClear(GL_COLOR_BUFFER_BIT)
        glClearColor(0.1, 0.1, 0.1, 1.0)
        for obj in self.objects.values():
            obj.render()

    def handle_cursor_pos(self, xpos, ypos):
        """Пробрасываем событие перемещения курсора объектам, которые его обрабатывают."""
        for obj in self.objects.values():
            if hasattr(obj, "handle_cursor_pos"):
                obj.handle_cursor_pos(xpos, ypos)

    def handle_mouse_button(self, button, action, mods):
        """Пробрасываем событие клика мыши объектам, которые его обрабатывают."""
        for obj in self.objects.values():
            if hasattr(obj, "handle_mouse_button"):
                obj.handle_mouse_button(button, action, mods)

    def cleanup(self):
        """Очистка ресурсов объектов при выходе."""
        for obj in self.objects.values():
            obj.cleanup()


# Ниже — просто тестовая сцена (как и было в исходнике).
class MyScene(Scene):
    def __init__(self):
        super().__init__()
        self.time = 0.0

        # Колбеки для кнопки
        def on_hover(button):
            button.color = np.array([1.0, 0.5, 0.5], dtype=np.float32)  # Светло-красный

        def on_press(button):
            button.color = np.array([0.5, 0.0, 0.0], dtype=np.float32)  # Темно-красный

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
        # Обновляем координаты других объектов, если они есть
        if "square1" in self.objects:
            self.objects["square1"].set_position(np.sin(self.time) * 0.5, 0.0)
        if "circle1" in self.objects:
            self.objects["circle1"].set_position(-np.sin(self.time) * 0.5, 0.0)
        if "square2" in self.objects:
            self.objects["square2"].set_position(0.0, np.cos(self.time) * 0.5)


if __name__ == "__main__":
    engine = GameEngine(800, 600, "Test with Button")
    scene = MyScene()

    # Добавляем другие объекты для теста (если они есть)
    scene.add_object(Square(name="square1"))
    scene.add_object(Circle(name="circle1"))
    scene.add_object(Square(name="square2"))

    engine.set_scene(scene)
    engine.run()
