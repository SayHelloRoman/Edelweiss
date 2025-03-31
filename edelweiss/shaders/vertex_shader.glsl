#version 330 core

layout (location = 0) in vec3 aPos; 
layout (location = 1) in vec2 aTexCoord;

out vec2 TexCoord; 

uniform vec3 u_position;
uniform float u_scale;

void main()
{
    gl_Position = vec4(aPos * u_scale + u_position, 1.0);
    TexCoord = aTexCoord; 
}