#version 330 core

layout (location = 0) in vec3 a_Position;
layout (location = 1) in float a_Level;
layout (location = 2) in vec2 a_TexCoord;

uniform mat4 u_PV;
uniform float u_Intensity;

out vec2 v_TexCoord;
out float v_Level;
out float v_Intensity;

void main()
{
    v_TexCoord = a_TexCoord;
    v_Level = a_Level;
    v_Intensity = u_Intensity;

    gl_Position = u_PV * vec4(a_Position, 1.0);
}
