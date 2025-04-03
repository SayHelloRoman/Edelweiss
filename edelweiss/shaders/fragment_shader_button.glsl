#version 330 core

in vec3 v_color;  // Цвет из вершинного шейдера

out vec4 FragColor;  // Конечный цвет пикселя

void main()
{
    FragColor = vec4(v_color, 1.0);  // Устанавливаем цвет пикселя
}