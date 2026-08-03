#version 330 core

// Per-instance attributes
layout (location = 0) in vec3 a_InstancePos;
layout (location = 1) in float a_InstanceSize;
layout (location = 2) in float a_InstanceType;
layout (location = 3) in vec4 a_InstanceColor;
layout (location = 4) in float a_InstanceLifeRatio;

uniform mat4 u_PV;
uniform vec3 u_CamPos;

out vec2 v_UV;
out float v_Type;
out vec4 v_Color;
out float v_LifeRatio;

// Quad corner offsets
const vec2 QUAD_CORNER[6] = vec2[6](
    vec2(-0.5,  0.5),
    vec2(-0.5, -0.5),
    vec2( 0.5, -0.5),
    vec2(-0.5,  0.5),
    vec2( 0.5, -0.5),
    vec2( 0.5,  0.5)
);

void main()
{
    int vertexID = gl_VertexID % 6;
    vec2 offset = QUAD_CORNER[vertexID];
    v_UV = offset + vec2(0.5);

    v_Type = a_InstanceType;
    v_Color = a_InstanceColor;
    v_LifeRatio = a_InstanceLifeRatio;

    // Billboard Quad orient to Camera View
    vec3 viewDir = normalize(u_CamPos - a_InstancePos);
    vec3 upDir = vec3(0.0, 1.0, 0.0);
    vec3 rightDir = normalize(cross(upDir, viewDir));
    vec3 trueUp = cross(viewDir, rightDir);

    vec3 worldPos = a_InstancePos;

    // Rain Streak Vertical Expansion
    if (a_InstanceType == 3.0) // RAIN
    {
        worldPos += (upDir * offset.y * 4.0 + rightDir * offset.x * 0.1) * a_InstanceSize;
    }
    else
    {
        worldPos += (rightDir * offset.x + trueUp * offset.y) * a_InstanceSize;
    }

    gl_Position = u_PV * vec4(worldPos, 1.0);
}
