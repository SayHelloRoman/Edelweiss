import glfw
import numpy as np
from OpenGL.GL import *
import random

class Button:
    def __init__(self, name, x, y, width, height, color, on_hover=None, on_press=None, on_click=None, outline_color=None, outline_width=0, radius=0.1, text=""):
        self.name = name
        self.position = np.array([x, y, 0.0], dtype=np.float32)
        self.width_pixels = width  # Сохраняем пиксельные размеры
        self.height_pixels = height
        self.width = width  # Изначально в пикселях, будет обновляться в нормализованных
        self.height = height
        self.base_color = np.array(color, dtype=np.float32)
        self.color = self.base_color.copy()
        self.outline_color = np.array(outline_color, dtype=np.float32) if outline_color else np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.outline_width = outline_width
        self.radius = min(radius, min(width, height) / 2)
        self.on_hover = on_hover
        self.on_press = on_press
        self.on_click = on_click
        self.text = text

        self.hovered = False
        self.pressed = False

        self.window = glfw.get_current_context()
        if not self.window:
            raise Exception("Нет текущего GLFW контекста!")

        self.update_position(x, y)
        self.setup_vertices()
        self.setup_opengl()
        self.setup_shader()

    def pixels_to_normalized_coordinates(self, x, y, width, height, window_width, window_height):
        norm_x = (x / window_width) * 2 - 1
        norm_y = 1 - (y / window_height) * 2
        norm_width = (width / window_width) * 2
        norm_height = (height / window_height) * 2
        return norm_x, norm_y, norm_width, norm_height

    def update_position(self, x, y):
        window_width, window_height = glfw.get_window_size(self.window)
        norm_x, norm_y, norm_width, norm_height = self.pixels_to_normalized_coordinates(
            x, y, self.width_pixels, self.height_pixels, window_width, window_height
        )
        self.position[:2] = np.array([norm_x, norm_y], dtype=np.float32)
        self.width = norm_width  # Нормализованные размеры для рендеринга и проверки
        self.height = norm_height
        print(f"Updated position: x={x}, y={y}, norm_x={norm_x}, norm_y={norm_y}, width={self.width}, height={self.height}")

    def set_position(self, x, y):
        self.update_position(x, y)

    def set_color(self, color):
        self.base_color = np.array(color, dtype=np.float32)
        if not self.hovered and not self.pressed:
            self.color = self.base_color.copy()

    def set_outline_color(self, color):
        self.outline_color = np.array(color, dtype=np.float32)

    def set_text(self, text):
        self.text = text

    def setup_vertices(self):
        half_width = self.width / 2.0
        half_height = self.height / 2.0
        radius = self.radius * min(self.width, self.height) / 2
        num_segments = 8

        self.vertices = []
        self.outline_vertices = []

        if radius == 0:
            self.vertices.extend([
                -half_width,  half_height, 0.0,
                 half_width,  half_height, 0.0,
                 half_width, -half_height, 0.0,
                -half_width,  half_height, 0.0,
                 half_width, -half_height, 0.0,
                -half_width, -half_height, 0.0
            ])
            self.outline_vertices = self.vertices[:12]
        else:
            outline = []
            center_x = half_width - radius
            center_y = half_height - radius
            for i in range(num_segments + 1):
                angle = np.pi / 2 - (i * np.pi / 2) / num_segments
                x = center_x + radius * np.cos(angle)
                y = center_y + radius * np.sin(angle)
                outline.extend([x, y, 0.0])

            center_x = half_width - radius
            center_y = -half_height + radius
            for i in range(num_segments + 1):
                angle = 0 - (i * np.pi / 2) / num_segments
                x = center_x + radius * np.cos(angle)
                y = center_y + radius * np.sin(angle)
                outline.extend([x, y, 0.0])

            center_x = -half_width + radius
            center_y = -half_height + radius
            for i in range(num_segments + 1):
                angle = -np.pi / 2 - (i * np.pi / 2) / num_segments
                x = center_x + radius * np.cos(angle)
                y = center_y + radius * np.sin(angle)
                outline.extend([x, y, 0.0])

            center_x = -half_width + radius
            center_y = half_height - radius
            for i in range(num_segments + 1):
                angle = np.pi - (i * np.pi / 2) / num_segments
                x = center_x + radius * np.cos(angle)
                y = center_y + radius * np.sin(angle)
                outline.extend([x, y, 0.0])

            self.outline_vertices = outline
            center = [0.0, 0.0, 0.0]
            for i in range(len(outline) // 3):
                next_i = (i + 1) % (len(outline) // 3)
                self.vertices.extend(center)
                self.vertices.extend(outline[i * 3:i * 3 + 3])
                self.vertices.extend(outline[next_i * 3:next_i * 3 + 3])

        self.vertices = np.array(self.vertices, dtype=np.float32)
        self.outline_vertices = np.array(self.outline_vertices, dtype=np.float32)

    def setup_shader(self):
        vertex_shader = """
        #version 330 core
        layout(location = 0) in vec3 aPos;
        uniform vec3 u_position;
        void main() {
            gl_Position = vec4(aPos + u_position, 1.0);
        }
        """
        fragment_shader = """
        #version 330 core
        out vec4 FragColor;
        uniform vec3 u_color;
        void main() {
            FragColor = vec4(u_color, 1.0);
        }
        """

        vertex_shader_id = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex_shader_id, vertex_shader)
        glCompileShader(vertex_shader_id)
        if not glGetShaderiv(vertex_shader_id, GL_COMPILE_STATUS):
            print(glGetShaderInfoLog(vertex_shader_id))

        fragment_shader_id = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader_id, fragment_shader)
        glCompileShader(fragment_shader_id)
        if not glGetShaderiv(fragment_shader_id, GL_COMPILE_STATUS):
            print(glGetShaderInfoLog(fragment_shader_id))

        self.shader = glCreateProgram()
        glAttachShader(self.shader, vertex_shader_id)
        glAttachShader(self.shader, fragment_shader_id)
        glLinkProgram(self.shader)
        glDeleteShader(vertex_shader_id)
        glDeleteShader(fragment_shader_id)

    def setup_opengl(self):
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.outline_vao = glGenVertexArrays(1)
        self.outline_vbo = glGenBuffers(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, None)
        glEnableVertexAttribArray(0)
        glBindVertexArray(0)

        glBindVertexArray(self.outline_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.outline_vbo)
        glBufferData(GL_ARRAY_BUFFER, self.outline_vertices.nbytes, self.outline_vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, None)
        glEnableVertexAttribArray(0)
        glBindVertexArray(0)

    def handle_cursor_pos(self, xpos, ypos):
        window_width, window_height = glfw.get_window_size(self.window)
        norm_x = (xpos / window_width) * 2 - 1
        norm_y = 1 - (ypos / window_height) * 2

        prev_hovered = self.hovered
        self.hovered = (self.position[0] - self.width / 2 <= norm_x <= self.position[0] + self.width / 2 and
                        self.position[1] - self.height / 2 <= norm_y <= self.position[1] + self.height / 2)
        print(f"Cursor pos: x={xpos}, y={ypos}, norm_x={norm_x}, norm_y={norm_y}, hovered={self.hovered}, pos={self.position}, width={self.width}, height={self.height}")

        if self.hovered and not prev_hovered and self.on_hover:
            self.on_hover(self)
        elif not self.hovered and prev_hovered:
            self.color = self.base_color

    def handle_mouse_button(self, button, action, mods):
        if button == glfw.MOUSE_BUTTON_LEFT:
            xpos, ypos = glfw.get_cursor_pos(self.window)
            window_width, window_height = glfw.get_window_size(self.window)
            norm_x = (xpos / window_width) * 2 - 1
            norm_y = 1 - (ypos / window_height) * 2
            self.hovered = (self.position[0] - self.width / 2 <= norm_x <= self.position[0] + self.width / 2 and
                            self.position[1] - self.height / 2 <= norm_y <= self.position[1] + self.height / 2)
            print(f"Mouse event: x={xpos}, y={ypos}, norm_x={norm_x}, norm_y={norm_y}, action={action}, pressed={self.pressed}, hovered={self.hovered}, pos={self.position}")

            if action == glfw.PRESS and self.hovered:
                self.pressed = True
                if self.on_press:
                    self.on_press(self)
            elif action == glfw.RELEASE and self.pressed and self.hovered:
                print("Click detected, calling on_click")
                self.on_click(self)
                self.pressed = False
                # Перепроверяем hovered после перемещения
                xpos, ypos = glfw.get_cursor_pos(self.window)
                norm_x = (xpos / window_width) * 2 - 1
                norm_y = 1 - (ypos / window_height) * 2
                self.hovered = (self.position[0] - self.width / 2 <= norm_x <= self.position[0] + self.width / 2 and
                                self.position[1] - self.height / 2 <= norm_y <= self.position[1] + self.height / 2)
                print(f"After click: hovered={self.hovered}, pos={self.position}")
                if self.hovered and self.on_hover:
                    self.on_hover(self)
                else:
                    self.color = self.base_color
            elif action == glfw.RELEASE:
                self.pressed = False

    def render(self):
        glUseProgram(self.shader)
        
        glUniform3fv(glGetUniformLocation(self.shader, "u_position"), 1, self.position)
        glUniform3fv(glGetUniformLocation(self.shader, "u_color"), 1, self.color)
        glBindVertexArray(self.vao)
        if self.radius == 0:
            glDrawArrays(GL_TRIANGLES, 0, 6)
        else:
            glDrawArrays(GL_TRIANGLES, 0, len(self.vertices) // 3)
        glBindVertexArray(0)

        if self.outline_width > 0:
            glUniform3fv(glGetUniformLocation(self.shader, "u_color"), 1, self.outline_color)
            glLineWidth(self.outline_width)
            glBindVertexArray(self.outline_vao)
            if self.radius == 0:
                glDrawArrays(GL_LINE_LOOP, 0, 4)
            else:
                glDrawArrays(GL_LINE_LOOP, 0, len(self.outline_vertices) // 3)
            glBindVertexArray(0)
        
        glUseProgram(0)

    def cleanup(self):
        if self.vao:
            glDeleteVertexArrays(1, [self.vao])
        if self.vbo:
            glDeleteBuffers(1, [self.vbo])
        if self.outline_vao:
            glDeleteVertexArrays(1, [self.outline_vao])
        if self.outline_vbo:
            glDeleteBuffers(1, [self.outline_vbo])
        if self.shader:
            glDeleteProgram(self.shader)