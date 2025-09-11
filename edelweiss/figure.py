from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import abc
import ctypes


def _gl_version_tuple():
    try:
        ver = glGetString(GL_VERSION)
        if not ver:
            return (2, 1)
        s = ver.decode("ascii", errors="ignore")
        # try to parse "MAJOR.MINOR"
        parts = s.split()
        for token in parts:
            if "." in token:
                try:
                    maj, minr = token.split(".", 1)
                    return (int(maj), int(minr[0]))
                except Exception:
                    continue
        return (2, 1)
    except Exception:
        return (2, 1)


def _make_shader_program():
    """Create a shader program compatible with modern (GLSL 330) or legacy (GLSL 120) contexts."""
    major, _ = _gl_version_tuple()
    use_modern = major >= 3

    if use_modern:
        vert_src = """
        #version 330 core
        layout(location = 0) in vec3 position;
        uniform vec3 u_position;
        uniform float u_scale;
        void main() {
            vec3 scaled_pos = position * u_scale;
            vec3 final_pos = scaled_pos + u_position;
            gl_Position = vec4(final_pos, 1.0);
        }
        """
        frag_src = """
        #version 330 core
        out vec4 color;
        uniform vec3 u_color;
        void main() {
            color = vec4(u_color, 1.0);
        }
        """
    else:
        # GLSL 1.20 (OpenGL 2.1): no layout qualifiers, use attribute + gl_FragColor
        vert_src = """
        #version 120
        attribute vec3 position;
        uniform vec3 u_position;
        uniform float u_scale;
        void main() {
            vec3 scaled_pos = position * u_scale;
            vec3 final_pos = scaled_pos + u_position;
            gl_Position = vec4(final_pos, 1.0);
        }
        """
        frag_src = """
        #version 120
        uniform vec3 u_color;
        void main() {
            gl_FragColor = vec4(u_color, 1.0);
        }
        """

    vs = compileShader(vert_src, GL_VERTEX_SHADER)
    fs = compileShader(frag_src, GL_FRAGMENT_SHADER)

    program = glCreateProgram()
    glAttachShader(program, vs)
    glAttachShader(program, fs)

    if not use_modern:
        # bind attribute index for legacy GLSL before linking
        glBindAttribLocation(program, 0, b"position")

    glLinkProgram(program)

    # shaders are attached; they can be deleted after link
    glDeleteShader(vs)
    glDeleteShader(fs)

    # Uniform locations
    loc_pos = glGetUniformLocation(program, "u_position")
    loc_scale = glGetUniformLocation(program, "u_scale")
    loc_color = glGetUniformLocation(program, "u_color")

    return program, loc_pos, loc_scale, loc_color, use_modern


class GameObject(abc.ABC):
    """Base abstract class for game objects"""

    def __init__(
        self, name=None, position=(0.0, 0.0, 0.0), color=(1.0, 0.5, 0.2), scale=1.0
    ):
        self.name = name if name else f"obj_{id(self)}"
        self.position = np.array(position, dtype=np.float32)
        self.color = np.array(color, dtype=np.float32)
        self.scale = float(scale)
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float32)

        self.vao = None
        self.vbo = None
        self.shader = None
        self._u_pos = None
        self._u_scale = None
        self._u_color = None
        self._has_vao = False
        self._vertex_count = 0

    def setup_shader(self):
        """Setup shaders considering color and position (with legacy fallback)."""
        self.shader, self._u_pos, self._u_scale, self._u_color, self._use_modern = (
            _make_shader_program()
        )

    @abc.abstractmethod
    def initialize(self):
        """Initialize geometry"""
        raise NotImplementedError

    @abc.abstractmethod
    def render(self):
        """Render the object"""
        raise NotImplementedError

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

    # helpers for VAO fallback
    def _try_make_vao(self):
        """Try to create VAO; legacy 2.1 may not support it."""
        self._has_vao = True
        try:
            self.vao = glGenVertexArrays(1)
            err = glGetError()
            if err != GL_NO_ERROR:
                self._has_vao = False
                self.vao = None
        except Exception:
            self._has_vao = False
            self.vao = None

    def _enable_attr_pointer(self):
        """Enable attribute 0 (position) with 3 floats, stride 12, offset 0."""
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))


class Square(GameObject):
    """Square class"""

    def initialize(self):
        vertices = np.array(
            [
                -0.5,
                0.5,
                0.0,  # Top-left
                0.5,
                0.5,
                0.0,  # Top-right
                -0.5,
                -0.5,
                0.0,  # Bottom-left
                0.5,
                -0.5,
                0.0,  # Bottom-right
            ],
            dtype=np.float32,
        )

        self.setup_shader()
        self._vertex_count = 4

        # buffers
        self._try_make_vao()
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        if self._has_vao:
            glBindVertexArray(self.vao)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            self._enable_attr_pointer()
            glBindVertexArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def render(self):
        glUseProgram(self.shader)
        glUniform3fv(self._u_pos, 1, self.position)
        glUniform1f(self._u_scale, self.scale)
        glUniform3fv(self._u_color, 1, self.color)

        if self._has_vao and self.vao:
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, self._vertex_count)
            glBindVertexArray(0)
        else:
            # no VAO path
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            self._enable_attr_pointer()
            glDrawArrays(GL_TRIANGLE_STRIP, 0, self._vertex_count)
            glDisableVertexAttribArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

        glUseProgram(0)


class Circle(GameObject):
    """Circle class"""

    def initialize(self):
        segments = 32
        verts = [0.0, 0.0, 0.0]  # center
        for i in range(segments + 1):
            angle = 2.0 * np.pi * i / segments
            x = 0.5 * np.cos(angle)
            y = 0.5 * np.sin(angle)
            verts.extend([x, y, 0.0])

        vertices = np.array(verts, dtype=np.float32)

        self.setup_shader()
        self._vertex_count = len(vertices) // 3

        self._try_make_vao()
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        if self._has_vao:
            glBindVertexArray(self.vao)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            self._enable_attr_pointer()
            glBindVertexArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def render(self):
        glUseProgram(self.shader)
        glUniform3fv(self._u_pos, 1, self.position)
        glUniform1f(self._u_scale, self.scale)
        glUniform3fv(self._u_color, 1, self.color)

        if self._has_vao and self.vao:
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLE_FAN, 0, self._vertex_count)
            glBindVertexArray(0)
        else:
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            self._enable_attr_pointer()
            glDrawArrays(GL_TRIANGLE_FAN, 0, self._vertex_count)
            glDisableVertexAttribArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

        glUseProgram(0)
