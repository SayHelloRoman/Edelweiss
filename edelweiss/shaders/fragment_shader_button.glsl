#version 330 core

in vec3 v_color;  // Color from the vertex shader

out vec4 FragColor;  // Final pixel color

void main()
{
    FragColor = vec4(v_color, 1.0);  // Set the pixel color
}
