from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import abc

class GameObject(abc.ABC):
    """Base abstract class for game objects"""
    def __init__(self, name=None, position=(0.0, 0.0, 0.0), color=(1.0, 0.5, 0.2), scale=1.0):
        self.name = name if name else f"obj_{id(self)}"  # Unique name by default
        self.position = np.array(position, dtype=np.float32)  # Position (x, y, z)
        self.color = np.array(color, dtype=np.float32)       # Color (r, g, b)
        self.scale = float(scale)                            # Scale
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.vao = None
        self.vbo = None
        self.shader = None

    def setup_shader(self):
        """Setup shaders considering color and position"""
        vertex_shader = """
        #version 450 core
        layout(location = 0) in vec3 position;
        uniform vec3 u_position;
        uniform float u_scale;
        void main() {
            vec3 scaled_pos = position * u_scale;
            vec3 final_pos = scaled_pos + u_position;
            gl_Position = vec4(final_pos, 1.0);
        }
        """
        fragment_shader = """
        #version 450 core
        out vec4 color;
        uniform vec3 u_color;
        void main() {
            color = vec4(u_color, 1.0);
        }
        """
        self.shader = compileProgram(
            compileShader(vertex_shader, GL_VERTEX_SHADER),
            compileShader(fragment_shader, GL_FRAGMENT_SHADER)
        )

    @abc.abstractmethod
    def initialize(self):
        """Initialize geometry"""
        pass

    @abc.abstractmethod
    def render(self):
        """Render the object"""
        pass

    def cleanup(self):
        """Clean up resources"""
        if self.vao:
            glDeleteVertexArrays(1, [self.vao])
        if self.vbo:
            glDeleteBuffers(1, [self.vbo])
        if self.shader:
            glDeleteProgram(self.shader)

    def set_position(self, x, y, z=0.0):
        """Set new position"""
        self.position = np.array([x, y, z], dtype=np.float32)

    def set_color(self, r, g, b):
        """Set new color"""
        self.color = np.array([r, g, b], dtype=np.float32)

    def set_scale(self, scale):
        """Set new scale"""
        self.scale = float(scale)


class Square(GameObject):
    """Square class"""
    def initialize(self):
        vertices = np.array([
            -0.5,  0.5, 0.0,  # Top-left
             0.5,  0.5, 0.0,  # Top-right
            -0.5, -0.5, 0.0,  # Bottom-left
             0.5, -0.5, 0.0   # Bottom-right
        ], dtype=np.float32)

        self.setup_shader()
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        glBindVertexArray(0)

    def render(self):
        print(self.shader)
        glUseProgram(self.shader)
        glUniform3fv(glGetUniformLocation(self.shader, "u_position"), 1, self.position)
        glUniform1f(glGetUniformLocation(self.shader, "u_scale"), self.scale)
        glUniform3fv(glGetUniformLocation(self.shader, "u_color"), 1, self.color)
        
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindVertexArray(0)
        glUseProgram(0)


class Circle(GameObject):
    """Circle class"""
    def initialize(self):
        segments = 32
        vertices = [0.0, 0.0, 0.0]  # Center of the circle
        for i in range(segments + 1):
            angle = 2.0 * np.pi * i / segments
            x = 0.5 * np.cos(angle)
            y = 0.5 * np.sin(angle)
            vertices.extend([x, y, 0.0])
        
        vertices = np.array(vertices, dtype=np.float32)

        self.setup_shader()
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        glBindVertexArray(0)

    def render(self):
        glUseProgram(self.shader)
        glUniform3fv(glGetUniformLocation(self.shader, "u_position"), 1, self.position)
        glUniform1f(glGetUniformLocation(self.shader, "u_scale"), self.scale)
        glUniform3fv(glGetUniformLocation(self.shader, "u_color"), 1, self.color)
        
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, 33)
        glBindVertexArray(0)
        glUseProgram(0)