from OpenGL.GL import glCreateShader, glShaderSource, glCompileShader, glGetShaderiv, GL_COMPILE_STATUS, glGetShaderInfoLog
from OpenGL.GL import glCreateProgram, glAttachShader, glLinkProgram, glGetProgramiv, GL_LINK_STATUS, glGetProgramInfoLog, glDeleteShader
from OpenGL.GL import GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, GL_COMPILE_STATUS, GL_LINK_STATUS


def load_shader(file_path):
    with open(file_path, 'r') as f:
        return f.read()
    
def compile_shader(shader_code, shader_type):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, shader_code)
    glCompileShader(shader)
    
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        print(f"Ошибка компиляции шейдера: {glGetShaderInfoLog(shader)}")
        return None
    return shader


def create_shader_program(vertex_shader_code, fragment_shader_code):
    vertex_shader = compile_shader(vertex_shader_code, GL_VERTEX_SHADER)
    fragment_shader = compile_shader(fragment_shader_code, GL_FRAGMENT_SHADER)
    
    if vertex_shader is None or fragment_shader is None:
        return None

    shader_program = glCreateProgram()
    glAttachShader(shader_program, vertex_shader)
    glAttachShader(shader_program, fragment_shader)
    glLinkProgram(shader_program)
    
    if not glGetProgramiv(shader_program, GL_LINK_STATUS):
        print(f"Ошибка линковки программы шейдера: {glGetProgramInfoLog(shader_program)}")
        return None

    # Удаляем шейдеры после линковки, они больше не нужны
    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)
    
    return shader_program