import glfw
from OpenGL.GL import *

def check_opengl():
    if not glfw.init():
        print("Не удалось инициализировать GLFW")
        return
    
    # Пробуем разные версии OpenGL
    for major, minor in [(4, 5), (3, 3), (2, 1)]:
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, major)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, minor)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)

        window = glfw.create_window(800, 600, "Test", None, None)
        if window:
            glfw.make_context_current(window)
            version = glGetString(GL_VERSION).decode('utf-8')
            print(f"Успешно создан контекст OpenGL {major}.{minor}: {version}")
            print(f"glGenVertexArrays доступен: {bool(glGenVertexArrays)}")
            glfw.destroy_window(window)
            break
        else:
            print(f"Не удалось создать контекст OpenGL {major}.{minor}")
    
    glfw.terminate()

if __name__ == "__main__":
    check_opengl()