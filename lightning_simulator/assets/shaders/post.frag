#version 330 core

in vec2 v_TexCoord;

uniform sampler2D u_SceneTexture;
uniform sampler2D u_BloomTexture;

uniform float u_Exposure;
uniform float u_BloomIntensity;
uniform float u_ChromaticAberration;
uniform float u_VignetteStrength;

out vec4 FragColor;

// ACES Film Tonemapping Curve
vec3 ACESFilm(vec3 x)
{
    float a = 2.51;
    float b = 0.03;
    float c = 2.43;
    float d = 0.59;
    float e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

// Pseudo-random Film Grain Generator
float filmGrain(vec2 uv)
{
    return (fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453) - 0.5) * 0.04;
}

void main()
{
    vec2 uv = v_TexCoord;

    // Chromatic Aberration Channel Shift
    vec2 distFromCenter = uv - vec2(0.5);
    vec2 shift = distFromCenter * u_ChromaticAberration;

    float r = texture(u_SceneTexture, uv + shift).r;
    float g = texture(u_SceneTexture, uv).g;
    float b = texture(u_SceneTexture, uv - shift).b;
    vec3 sceneColor = vec3(r, g, b);

    // Composite Bloom Glow
    vec3 bloomColor = texture(u_BloomTexture, uv).rgb;
    sceneColor += bloomColor * u_BloomIntensity;

    // Exposure adjustment
    sceneColor *= u_Exposure;

    // Tonemapping (ACES)
    vec3 mapped = ACESFilm(sceneColor);

    // Vignette
    float vignette = 1.0 - dot(distFromCenter, distFromCenter) * u_VignetteStrength * 1.5;
    mapped *= clamp(vignette, 0.0, 1.0);

    // Film Grain
    mapped += vec3(filmGrain(uv));

    // Gamma Correction
    mapped = pow(mapped, vec3(1.0 / 2.2));

    FragColor = vec4(mapped, 1.0);
}
