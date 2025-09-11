#version 330 core

layout(location = 0) in vec3 a_position;  // Vertex position
layout(location = 1) in vec3 a_color;     // Vertex color

out vec3 v_color;  // Color to pass to the fragment shader

uniform vec3 u_position;

void main()
{
    gl_Position = vec4(a_position + u_position, 1.0);  // Shift position by button coordinates
    v_color = a_color;  // Pass the color to the fragment shader
}
