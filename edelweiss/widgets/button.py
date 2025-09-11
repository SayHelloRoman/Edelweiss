import glfw
import numpy as np
from OpenGL.GL import *
import ctypes


class Button:
    def __init__(
        self,
        name,
        x,
        y,
        width,
        height,
        color,
        on_hover=None,
        on_press=None,
        on_click=None,
        outline_color=None,
        outline_width=0,
        radius=0.1,
        text="",
    ):
        self.name = name
        self.position = np.array(
            [0.0, 0.0, 0.0], dtype=np.float32
        )  # will be set via update_position
        self.width_pixels = width
        self.height_pixels = height
        self.width = float(width)  # normalized width (computed in update_position)
        self.height = float(height)  # normalized height (computed in update_position)

        self.base_color = np.array(color, dtype=np.float32)
        self.color = self.base_color.copy()
        self.outline_color = (
            np.array(outline_color, dtype=np.float32)
            if outline_color is not None
            else np.array([0.0, 0.0, 0.0], dtype=np.float32)
        )
        self.outline_width = float(outline_width)
        self.radius = float(min(radius, min(width, height) / 2.0))
        self.on_hover = on_hover
        self.on_press = on_press
        self.on_click = on_click
        self.text = text

        self.hovered = False
        self.pressed = False

        self.window = glfw.get_current_context()
        if not self.window:
            raise Exception(
                "No current GLFW context. Create window and make context current before creating Button."
            )

        # GL resources (created in initialize)
        self.shader = None
        self._u_pos = None
        self._u_color = None

        self.vao = None
        self.vbo = None
        self.outline_vao = None
        self.outline_vbo = None
        self._has_vao = False  # fallback flag for GL 2.1

        # geometry
        self.vertices = None
        self.outline_vertices = None

        # compute normalized position/size and CPU-side geometry now
        self.update_position(x, y)
        self.setup_vertices()

    # -------- lifecycle called by engine after GL context is active --------
    def initialize(self):
        """Called by engine after context is current. Safe place to touch OpenGL."""
        self.setup_shader()
        self.setup_opengl()

    # -------------------- helpers: coordinates & geometry -------------------
    def pixels_to_normalized_coordinates(
        self, x, y, width, height, window_width, window_height
    ):
        # convert pixel-space into NDC [-1,1] coords
        norm_x = (x / window_width) * 2.0 - 1.0
        norm_y = 1.0 - (y / window_height) * 2.0
        norm_width = (width / window_width) * 2.0
        norm_height = (height / window_height) * 2.0
        return norm_x, norm_y, norm_width, norm_height

    def update_position(self, x, y):
        window_width, window_height = glfw.get_window_size(self.window)
        norm_x, norm_y, norm_w, norm_h = self.pixels_to_normalized_coordinates(
            x, y, self.width_pixels, self.height_pixels, window_width, window_height
        )
        self.position[:2] = np.array([norm_x, norm_y], dtype=np.float32)
        self.width = norm_w
        self.height = norm_h

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
        """Build CPU-side vertex arrays for body (triangles) and outline (line-loop points)."""
        half_width = self.width / 2.0
        half_height = self.height / 2.0
        radius = self.radius * min(self.width, self.height) / 2.0
        num_segments = 8  # corner smoothness

        verts = []
        outline = []

        if radius <= 1e-7:
            # simple rectangle (two triangles)
            verts.extend(
                [
                    -half_width,
                    half_height,
                    0.0,
                    half_width,
                    half_height,
                    0.0,
                    half_width,
                    -half_height,
                    0.0,
                    -half_width,
                    half_height,
                    0.0,
                    half_width,
                    -half_height,
                    0.0,
                    -half_width,
                    -half_height,
                    0.0,
                ]
            )
            # outline = rectangle corners
            outline.extend(
                [
                    -half_width,
                    half_height,
                    0.0,
                    half_width,
                    half_height,
                    0.0,
                    half_width,
                    -half_height,
                    0.0,
                    -half_width,
                    -half_height,
                    0.0,
                ]
            )
        else:
            # build rounded rectangle outline (four quarter-circles)
            def arc(cx, cy, start_angle, end_angle, segments):
                for i in range(segments + 1):
                    t = i / float(segments)
                    ang = start_angle + t * (end_angle - start_angle)
                    x = cx + radius * np.cos(ang)
                    y = cy + radius * np.sin(ang)
                    outline.extend([x, y, 0.0])

            # centers for the 4 corners
            arc(
                half_width - radius, half_height - radius, np.pi / 2, 0.0, num_segments
            )  # top-right
            arc(
                half_width - radius,
                -half_height + radius,
                0.0,
                -np.pi / 2,
                num_segments,
            )  # bottom-right
            arc(
                -half_width + radius,
                -half_height + radius,
                -np.pi / 2,
                -np.pi,
                num_segments,
            )  # bottom-left
            arc(
                -half_width + radius,
                half_height - radius,
                -np.pi,
                -3 * np.pi / 2,
                num_segments,
            )  # top-left

            # fill: triangle fan from center following outline
            center = [0.0, 0.0, 0.0]
            count = len(outline) // 3
            for i in range(count):
                nxt = (i + 1) % count
                verts.extend(center)
                verts.extend(outline[i * 3 : i * 3 + 3])
                verts.extend(outline[nxt * 3 : nxt * 3 + 3])

        self.vertices = np.array(verts, dtype=np.float32)
        self.outline_vertices = np.array(outline, dtype=np.float32)

    # ----------------------------- shaders ----------------------------------
    def _gl_version(self):
        try:
            ver = glGetString(GL_VERSION)
            if not ver:
                return (2, 1)  # safest fallback
            s = ver.decode("ascii", errors="ignore")
            # try parse "MAJOR.MINOR"
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

    def setup_shader(self):
        """Compile shaders. Use GLSL 330 if available, otherwise fallback to GLSL 120."""
        major, minor = self._gl_version()
        use_modern = major >= 3  # 3.x+ usually supports 330 core on macOS profiles

        if use_modern:
            vert_src = """
            #version 330 core
            layout(location = 0) in vec3 aPos;
            uniform vec3 u_position;
            void main() {
                gl_Position = vec4(aPos + u_position, 1.0);
            }
            """
            frag_src = """
            #version 330 core
            out vec4 FragColor;
            uniform vec3 u_color;
            void main() {
                FragColor = vec4(u_color, 1.0);
            }
            """
        else:
            # GLSL 1.20 (OpenGL 2.1) — no layout qualifiers, use attribute/varying
            vert_src = """
            #version 120
            attribute vec3 aPos;
            uniform vec3 u_position;
            void main() {
                gl_Position = vec4(aPos + u_position, 1.0);
            }
            """
            frag_src = """
            #version 120
            uniform vec3 u_color;
            void main() {
                gl_FragColor = vec4(u_color, 1.0);
            }
            """

        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, vert_src)
        glCompileShader(vs)
        if not glGetShaderiv(vs, GL_COMPILE_STATUS):
            info = glGetShaderInfoLog(vs)
            raise RuntimeError(f"Vertex shader compilation failed: {info}")

        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, frag_src)
        glCompileShader(fs)
        if not glGetShaderiv(fs, GL_COMPILE_STATUS):
            info = glGetShaderInfoLog(fs)
            raise RuntimeError(f"Fragment shader compilation failed: {info}")

        self.shader = glCreateProgram()
        glAttachShader(self.shader, vs)
        glAttachShader(self.shader, fs)

        if not use_modern:
            # bind attribute location for aPos before linking (since no layout(...) in 120)
            glBindAttribLocation(self.shader, 0, b"aPos")

        glLinkProgram(self.shader)
        glDeleteShader(vs)
        glDeleteShader(fs)

        if not glGetProgramiv(self.shader, GL_LINK_STATUS):
            info = glGetProgramInfoLog(self.shader)
            raise RuntimeError(f"Shader program link failed: {info}")

        # cache uniforms
        self._u_pos = glGetUniformLocation(self.shader, "u_position")
        self._u_color = glGetUniformLocation(self.shader, "u_color")

    # ----------------------------- OpenGL buffers ---------------------------
    def setup_opengl(self):
        """Create buffers. Try VAO; if invalid operation, fallback to no-VAO path."""
        # Try VAO
        self._has_vao = True
        try:
            # Some 2.1 contexts will still export glGenVertexArrays symbol but return INVALID_OPERATION.
            self.vao = glGenVertexArrays(1)
            err = glGetError()
            if err != GL_NO_ERROR:
                # VAO not supported in this context
                self._has_vao = False
                self.vao = None
        except Exception:
            self._has_vao = False
            self.vao = None

        # VBOs (available since GL 1.5)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(
            GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW
        )

        if self._has_vao:
            glBindVertexArray(self.vao)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
            glBindVertexArray(0)

        # outline buffer
        if self.outline_vertices is not None and len(self.outline_vertices) > 0:
            # try VAO for outline
            if self._has_vao:
                try:
                    self.outline_vao = glGenVertexArrays(1)
                    err = glGetError()
                    if err != GL_NO_ERROR:
                        self.outline_vao = None
                except Exception:
                    self.outline_vao = None
            self.outline_vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.outline_vbo)
            glBufferData(
                GL_ARRAY_BUFFER,
                self.outline_vertices.nbytes,
                self.outline_vertices,
                GL_STATIC_DRAW,
            )

            if self._has_vao and self.outline_vao:
                glBindVertexArray(self.outline_vao)
                glBindBuffer(GL_ARRAY_BUFFER, self.outline_vbo)
                glEnableVertexAttribArray(0)
                glVertexAttribPointer(
                    0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0)
                )
                glBindVertexArray(0)

        # unbind
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    # ----------------------------- input handlers ---------------------------
    def handle_cursor_pos(self, xpos, ypos):
        window_width, window_height = glfw.get_window_size(self.window)
        norm_x = (xpos / window_width) * 2 - 1
        norm_y = 1 - (ypos / window_height) * 2

        prev_hovered = self.hovered
        self.hovered = (
            self.position[0] - self.width / 2
            <= norm_x
            <= self.position[0] + self.width / 2
            and self.position[1] - self.height / 2
            <= norm_y
            <= self.position[1] + self.height / 2
        )

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
            self.hovered = (
                self.position[0] - self.width / 2
                <= norm_x
                <= self.position[0] + self.width / 2
                and self.position[1] - self.height / 2
                <= norm_y
                <= self.position[1] + self.height / 2
            )

            if action == glfw.PRESS and self.hovered:
                self.pressed = True
                if self.on_press:
                    self.on_press(self)
            elif action == glfw.RELEASE and self.pressed and self.hovered:
                if self.on_click:
                    self.on_click(self)
                self.pressed = False
                # re-evaluate hover state after potential move
                xpos, ypos = glfw.get_cursor_pos(self.window)
                norm_x = (xpos / window_width) * 2 - 1
                norm_y = 1 - (ypos / window_height) * 2
                self.hovered = (
                    self.position[0] - self.width / 2
                    <= norm_x
                    <= self.position[0] + self.width / 2
                    and self.position[1] - self.height / 2
                    <= norm_y
                    <= self.position[1] + self.height / 2
                )
                if self.hovered and self.on_hover:
                    self.on_hover(self)
                else:
                    self.color = self.base_color
            elif action == glfw.RELEASE:
                self.pressed = False

    # -------------------------------- render --------------------------------
    def render(self):
        glUseProgram(self.shader)
        glUniform3fv(self._u_pos, 1, self.position)
        glUniform3fv(self._u_color, 1, self.color)

        if self._has_vao and self.vao:
            glBindVertexArray(self.vao)
            if self.radius <= 1e-7:
                glDrawArrays(GL_TRIANGLES, 0, 6)
            else:
                glDrawArrays(GL_TRIANGLES, 0, len(self.vertices) // 3)
            glBindVertexArray(0)
        else:
            # no VAO: set attribute pointers each frame
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
            if self.radius <= 1e-7:
                glDrawArrays(GL_TRIANGLES, 0, 6)
            else:
                glDrawArrays(GL_TRIANGLES, 0, len(self.vertices) // 3)
            glDisableVertexAttribArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

        if (
            self.outline_width > 0
            and self.outline_vertices is not None
            and len(self.outline_vertices) > 0
        ):
            glUniform3fv(self._u_color, 1, self.outline_color)
            glLineWidth(self.outline_width)

            if self._has_vao and self.outline_vao:
                glBindVertexArray(self.outline_vao)
                glDrawArrays(GL_LINE_LOOP, 0, len(self.outline_vertices) // 3)
                glBindVertexArray(0)
            else:
                glBindBuffer(GL_ARRAY_BUFFER, self.outline_vbo)
                glEnableVertexAttribArray(0)
                glVertexAttribPointer(
                    0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0)
                )
                glDrawArrays(GL_LINE_LOOP, 0, len(self.outline_vertices) // 3)
                glDisableVertexAttribArray(0)
                glBindBuffer(GL_ARRAY_BUFFER, 0)

        glUseProgram(0)

    # ------------------------------- cleanup --------------------------------
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
