#version 330 core

layout(location = 0) in vec3 a_position;  // Позиция вершины
layout(location = 1) in vec3 a_color;     // Цвет вершины

out vec3 v_color;  // Цвет для передачи в фрагментный шейдер

uniform vec3 u_position;

void main()
{
    gl_Position = vec4(a_position + u_position, 1.0);  // Сдвигаем позицию с учетом координат кнопки
    v_color = a_color;  // Передаем цвет в фрагментный шейдер
}