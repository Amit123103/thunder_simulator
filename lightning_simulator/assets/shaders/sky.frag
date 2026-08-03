#version 330 core

in vec2 v_TexCoord;

uniform mat4 u_InverseViewProj;
uniform vec3 u_CamPos;
uniform vec3 u_SunDir;
uniform vec3 u_Rayleigh;
uniform float u_Mie;
uniform float u_MieG;
uniform float u_FlashIntensity;

out vec4 FragColor;

void main()
{
    // Reconstruct Ray Direction from screen quad
    vec4 clipPos = vec4(v_TexCoord * 2.0 - 1.0, 1.0, 1.0);
    vec4 viewPos = u_InverseViewProj * clipPos;
    vec3 rayDir = normalize(viewPos.xyz / viewPos.w - u_CamPos);

    float cosTheta = dot(rayDir, normalize(u_SunDir));

    // Rayleigh Phase
    float rPhase = 0.75 * (1.0 + cosTheta * cosTheta);

    // Mie Phase (Henyey-Greenstein)
    float g2 = u_MieG * u_MieG;
    float mPhase = (1.0 - g2) / pow(1.0 + g2 - 2.0 * u_MieG * cosTheta, 1.5);

    // Sky gradient color synthesis
    vec3 rayleighColor = u_Rayleigh * rPhase * 8.0;
    vec3 mieColor = vec3(u_Mie) * mPhase * vec3(1.0, 0.9, 0.7);

    // Dark twilight storm sky background color tint
    vec3 zenithColor = vec3(0.015, 0.03, 0.07);
    vec3 horizonColor = vec3(0.06, 0.10, 0.16);
    float heightFactor = clamp(rayDir.y, 0.0, 1.0);
    vec3 skyBase = mix(horizonColor, zenithColor, heightFactor);

    vec3 finalSky = skyBase + rayleighColor + mieColor;

    // Atmospheric Lightning Strobe Flash Illumination Tint
    if (u_FlashIntensity > 0.005)
    {
        vec3 flashColor = vec3(0.65, 0.82, 1.25);
        finalSky += flashColor * u_FlashIntensity * 1.4;
    }

    FragColor = vec4(finalSky, 1.0);
}
