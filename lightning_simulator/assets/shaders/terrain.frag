#version 330 core

in vec3 v_WorldPos;
in vec3 v_Normal;
in vec3 v_Tangent;
in vec3 v_Bitangent;
in vec2 v_TexCoord;

uniform vec3 u_CamPos;
uniform vec3 u_SunDir;
uniform vec3 u_FogColor;
uniform float u_FogDensity;

// Textures
uniform sampler2D u_NormalMap;
uniform sampler2D u_AOMap;
uniform sampler2D u_HeatMap;
uniform sampler2D u_ScorchMap;

// Dynamic Lightning Point Lights
uniform int u_NumLightningLights;
uniform vec3 u_LightningLightPos[8];
uniform float u_LightningLightIntensity[8];

out vec4 FragColor;

const vec3 ROCK_BASE_COLOR = vec3(0.18, 0.16, 0.15);
const vec3 DIRT_COLOR = vec3(0.12, 0.10, 0.08);
const vec3 MOLTEN_LAVA_COLOR = vec3(1.0, 0.35, 0.05);

void main()
{
    // Normalized grid UV coordinates (0.0 to 1.0)
    vec2 gridUV = v_WorldPos.xz / 120.0 + 0.5;

    // Sample Textures
    vec3 mapNormal = texture(u_NormalMap, gridUV).rgb * 2.0 - 1.0;
    float ao = texture(u_AOMap, gridUV).r;
    float heat = texture(u_HeatMap, gridUV).r;
    float scorch = texture(u_ScorchMap, gridUV).r;

    // Construct TBN Matrix
    mat3 TBN = mat3(normalize(v_Tangent), normalize(v_Bitangent), normalize(v_Normal));
    vec3 N = normalize(TBN * mapNormal);
    vec3 V = normalize(u_CamPos - v_WorldPos);
    vec3 L_sun = normalize(u_SunDir);

    // Albedo Color with Scorch Mark Blending
    vec3 albedo = mix(ROCK_BASE_COLOR, DIRT_COLOR, clamp(v_WorldPos.y / 28.0, 0.0, 1.0));
    albedo = mix(albedo, vec3(0.02, 0.02, 0.03), scorch * 0.85);  // Blackened carbon scorch

    // Sun Directional Light Diffuse + Specular
    float NdotL = max(dot(N, L_sun), 0.0);
    vec3 diffuseSun = vec3(0.9, 0.85, 0.75) * NdotL * 0.6;

    vec3 H_sun = normalize(L_sun + V);
    float specSun = pow(max(dot(N, H_sun), 0.0), 32.0) * 0.2;

    // Lighting Accumulation
    vec3 totalLighting = (diffuseSun + vec3(specSun)) * ao;

    // Dynamic Lightning Point Lights Illumination
    for (int i = 0; i < u_NumLightningLights; ++i)
    {
        vec3 lightDir = u_LightningLightPos[i] - v_WorldPos;
        float dist = length(lightDir);
        lightDir = normalize(lightDir);

        float atten = 1.0 / (1.0 + 0.05 * dist + 0.008 * dist * dist);
        float NdotL_light = max(dot(N, lightDir), 0.0);

        totalLighting += vec3(0.65, 0.8, 1.0) * NdotL_light * atten * u_LightningLightIntensity[i];
    }

    // Ambient Lighting
    vec3 ambient = vec3(0.08, 0.1, 0.15) * albedo * ao;
    vec3 finalColor = ambient + albedo * totalLighting;

    // Molten Glowing Ground Emission (Heat Map)
    if (heat > 0.01)
    {
        vec3 emissiveGlow = MOLTEN_LAVA_COLOR * pow(heat, 1.5) * 8.0;
        finalColor += emissiveGlow;
    }

    // Exponential Height Fog
    float distToCam = length(u_CamPos - v_WorldPos);
    float fogFactor = 1.0 - exp(-distToCam * u_FogDensity);
    finalColor = mix(finalColor, u_FogColor, clamp(fogFactor, 0.0, 0.95));

    FragColor = vec4(finalColor, 1.0);
}
