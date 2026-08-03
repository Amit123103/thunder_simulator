#version 330 core

layout (location = 0) in vec3 a_Position;
layout (location = 1) in vec3 a_Normal;
layout (location = 2) in vec2 a_TexCoord;

uniform mat4 u_PV;
uniform mat4 u_Model;
uniform float u_Time;

out vec3 v_WorldPos;
out vec3 v_Normal;
out vec2 v_TexCoord;

void main()
{
    vec3 pos = a_Position;

    // Animated water surface wave displacement
    float wave1 = sin(pos.x * 2.0 + u_Time * 4.0) * 0.15;
    float wave2 = cos(pos.z * 2.5 + u_Time * 3.5) * 0.12;
    pos.y += wave1 + wave2;

    vec4 worldPos = u_Model * vec4(pos, 1.0);
    v_WorldPos = worldPos.xyz;
    
    mat3 normalMatrix = transpose(inverse(mat3(u_Model)));
    v_Normal = normalize(normalMatrix * a_Normal);
    
    // UV scrolling for cascading water flow
    v_TexCoord = a_TexCoord + vec2(0.0, u_Time * 1.2);

    gl_Position = u_PV * worldPos;
}
