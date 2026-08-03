#version 330 core

in vec3 v_WorldPos;
in vec3 v_Normal;
in vec2 v_TexCoord;

uniform vec3 u_CamPos;
uniform vec3 u_SunDir;
uniform float u_Time;
uniform vec3 u_FogColor;
uniform float u_FogDensity;

// Dynamic Lightning Point Lights
uniform int u_NumLightningLights;
uniform vec3 u_LightningLightPos[8];
uniform float u_LightningLightIntensity[8];

out vec4 FragColor;

const vec3 WATER_DEEP = vec3(0.03, 0.22, 0.38);
const vec3 WATER_SHALLOW = vec3(0.12, 0.55, 0.72);
const vec3 FOAM_COLOR = vec3(0.88, 0.95, 1.0);

// Procedural foam pattern
float sampleFoamPattern(vec2 uv)
{
    float f1 = sin(uv.x * 25.0 + u_Time * 6.0) * cos(uv.y * 18.0 - u_Time * 8.0);
    float f2 = sin(uv.y * 40.0 + u_Time * 12.0) * 0.5;
    return clamp((f1 + f2 + 0.3) * 1.5, 0.0, 1.0);
}

void main()
{
    vec3 N = normalize(v_Normal);
    vec3 V = normalize(u_CamPos - v_WorldPos);
    vec3 L_sun = normalize(u_SunDir);

    // Fresnel Reflection Factor
    float NdotV = max(dot(N, V), 0.0);
    float fresnel = pow(1.0 - NdotV, 3.0);
    fresnel = clamp(fresnel, 0.15, 0.85);

    // Cascading Water Foam Blending
    float foam = sampleFoamPattern(v_TexCoord);
    vec3 baseWaterColor = mix(WATER_DEEP, WATER_SHALLOW, 0.4);
    vec3 waterColor = mix(baseWaterColor, FOAM_COLOR, foam * 0.65);

    // Sun Specular Highlight
    vec3 H_sun = normalize(L_sun + V);
    float specSun = pow(max(dot(N, H_sun), 0.0), 128.0) * 2.5;
    vec3 lighting = vec3(specSun) * vec3(1.0, 0.95, 0.85);

    // Lightning Flash Reflections on Waterfall & Basin Surface
    for (int i = 0; i < u_NumLightningLights; ++i)
    {
        vec3 lightDir = u_LightningLightPos[i] - v_WorldPos;
        float dist = length(lightDir);
        lightDir = normalize(lightDir);

        float atten = 1.0 / (1.0 + 0.03 * dist + 0.005 * dist * dist);
        vec3 H_light = normalize(lightDir + V);
        float specLight = pow(max(dot(N, H_light), 0.0), 96.0) * 3.5;

        vec3 electricReflect = vec3(0.7, 0.9, 1.35) * (specLight + atten * 0.4);
        lighting += electricReflect * u_LightningLightIntensity[i];
    }

    vec3 finalColor = mix(waterColor, vec3(0.4, 0.6, 0.8), fresnel * 0.5) + lighting;

    // Height Fog
    float distToCam = length(u_CamPos - v_WorldPos);
    float fogFactor = 1.0 - exp(-distToCam * u_FogDensity);
    finalColor = mix(finalColor, u_FogColor, clamp(fogFactor, 0.0, 0.95));

    FragColor = vec4(finalColor, 0.85 + foam * 0.15);
}
