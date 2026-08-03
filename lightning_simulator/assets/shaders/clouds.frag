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

// Henyey-Greenstein Phase Function for Cloud Forward Scattering
float phaseHenyeyGreenstein(float cosTheta, float g)
{
    float g2 = g * g;
    return (1.0 - g2) / (4.0 * 3.14159265 * pow(1.0 + g2 - 2.0 * g * cosTheta, 1.5));
}

// Procedural 3D noise approximation
float sampleCloudNoise(vec3 pos)
{
    vec3 p = (pos + u_WindOffset) * 0.05;
    float n1 = sin(p.x) * cos(p.y) * sin(p.z);
    float n2 = sin(p.x * 2.3 + 1.2) * cos(p.z * 1.8 + 0.5) * 0.5;
    float density = clamp((n1 + n2 + 0.3) * u_CloudDensity - (1.0 - u_CloudCoverage), 0.0, 1.0);
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
    const int STEPS = 32;
    float stepSize = (tMax - tMin) / float(STEPS);
    vec3 currentPos = u_CamPos + rayDir * tMin;

    vec4 accumulatedColor = vec4(0.0);
    float cosThetaSun = dot(rayDir, normalize(u_SunDir));
    float sunPhase = phaseHenyeyGreenstein(cosThetaSun, 0.65);

    for (int i = 0; i < STEPS; ++i)
    {
        float density = sampleCloudNoise(currentPos);
        if (density > 0.01)
        {
            // Internal Lightning Flash Illumination inside cloud volume
            vec3 lightToPos = currentPos - u_InternalLightPos;
            float distToLightning = length(lightToPos);
            float internalFlashAtten = 1.0 / (1.0 + 0.02 * distToLightning + 0.002 * distToLightning * distToLightning);
            vec3 internalFlash = vec3(0.7, 0.85, 1.2) * u_InternalLightIntensity * internalFlashAtten;

            // Direct Sun Scattering
            vec3 sunScattering = vec3(0.4, 0.45, 0.5) * sunPhase * 1.5;

            // Ambient Shadowing
            vec3 stepColor = (sunScattering + internalFlash + vec3(0.12, 0.15, 0.2)) * density;
            float alpha = density * 0.15;

            accumulatedColor.rgb += stepColor * (1.0 - accumulatedColor.a) * alpha;
            accumulatedColor.a += (1.0 - accumulatedColor.a) * alpha;

            if (accumulatedColor.a >= 0.95) break;
        }

        currentPos += rayDir * stepSize;
    }

    FragColor = accumulatedColor;
}
