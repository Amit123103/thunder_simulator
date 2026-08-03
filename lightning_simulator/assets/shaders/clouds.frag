#version 330 core

in vec2 v_TexCoord;

uniform vec3 u_CamPos;
uniform mat4 u_InverseViewProj;

uniform float u_CloudMinHeight;
uniform float u_CloudMaxHeight;
uniform float u_CloudDensity;
uniform float u_CloudCoverage;
uniform vec3 u_WindOffset;

uniform vec3 u_SunDir;
uniform vec3 u_InternalLightPos;
uniform float u_InternalLightIntensity;

out vec4 FragColor;

// Dual Henyey-Greenstein Phase Function for Silver-Lining Cloud Scattering
float phaseHenyeyGreenstein(float cosTheta, float g)
{
    float g2 = g * g;
    return (1.0 - g2) / (4.0 * 3.14159265 * pow(1.0 + g2 - 2.0 * g * cosTheta, 1.5));
}

float dualPhase(float cosTheta)
{
    // Combine forward silver-lining glare (g=0.65) and back-scatter (g=-0.30)
    return mix(phaseHenyeyGreenstein(cosTheta, 0.65), phaseHenyeyGreenstein(cosTheta, -0.30), 0.3);
}

// Multi-Frequency 3D FBM Storm Cloud Noise Generator
float sampleCloudNoise(vec3 pos)
{
    vec3 p = (pos + u_WindOffset) * 0.04;
    
    // Octave 1: Coarse Cloud Macro Shape
    float n1 = sin(p.x) * cos(p.y) * sin(p.z);
    
    // Octave 2: Puffy Cumulus Billows
    float n2 = sin(p.x * 2.3 + 1.2) * cos(p.y * 2.1 + 0.8) * sin(p.z * 1.9 + 0.4) * 0.5;
    
    // Octave 3: Micro Detail Turbulence
    float n3 = sin(p.x * 4.8 + 2.5) * cos(p.z * 4.2 + 1.9) * 0.25;

    float totalNoise = n1 + n2 + n3;

    // Height gradient envelope (Dark flat bottom, puffy middle, anvil top)
    float normHeight = (pos.y - u_CloudMinHeight) / (u_CloudMaxHeight - u_CloudMinHeight);
    float heightEnvelope = sin(clamp(normHeight, 0.0, 1.0) * 3.14159265);

    float density = clamp((totalNoise + 0.45) * heightEnvelope * u_CloudDensity - (1.0 - u_CloudCoverage), 0.0, 1.0);
    return density;
}

void main()
{
    // Reconstruct Ray Direction from screen coordinates
    vec4 clipPos = vec4(v_TexCoord * 2.0 - 1.0, -1.0, 1.0);
    vec4 viewPos = u_InverseViewProj * clipPos;
    vec3 rayDir = normalize(viewPos.xyz / viewPos.w - u_CamPos);

    if (rayDir.y <= 0.0)
    {
        discard; // Ray pointing down into terrain
    }

    // Intersect ray with cloud layer planes
    float tMin = (u_CloudMinHeight - u_CamPos.y) / rayDir.y;
    float tMax = (u_CloudMaxHeight - u_CamPos.y) / rayDir.y;

    if (tMin < 0.0) tMin = 0.0;
    if (tMax <= tMin) discard;

    // Raymarching Steps
    const int STEPS = 36;
    float stepSize = (tMax - tMin) / float(STEPS);
    vec3 currentPos = u_CamPos + rayDir * tMin;

    vec4 accumulatedColor = vec4(0.0);
    float cosThetaSun = dot(rayDir, normalize(u_SunDir));
    float sunPhase = dualPhase(cosThetaSun);

    for (int i = 0; i < STEPS; ++i)
    {
        float density = sampleCloudNoise(currentPos);
        if (density > 0.015)
        {
            // Internal Lightning Flash Illumination inside storm cloud volume
            vec3 lightToPos = currentPos - u_InternalLightPos;
            float distToLightning = length(lightToPos);
            float internalFlashAtten = 1.0 / (1.0 + 0.015 * distToLightning + 0.001 * distToLightning * distToLightning);
            vec3 internalFlash = vec3(0.75, 0.90, 1.35) * u_InternalLightIntensity * internalFlashAtten * 2.0;

            // Direct Sun Silver-Lining Scattering
            vec3 sunScattering = vec3(0.45, 0.48, 0.55) * sunPhase * 1.8;

            // Dark Storm Cloud Self-Shadowing Ambient Color
            vec3 cloudBaseColor = vec3(0.06, 0.08, 0.12);

            vec3 stepColor = (cloudBaseColor + sunScattering + internalFlash) * density;
            float alpha = density * 0.18;

            accumulatedColor.rgb += stepColor * (1.0 - accumulatedColor.a) * alpha;
            accumulatedColor.a += (1.0 - accumulatedColor.a) * alpha;

            if (accumulatedColor.a >= 0.95) break;
        }

        currentPos += rayDir * stepSize;
    }

    FragColor = accumulatedColor;
}
