#version 330 core

in vec2 v_TexCoord;
in float v_Level;
in float v_Intensity;

out vec4 FragColor;

void main()
{
    // Distance from central axis of lightning ribbon [0.0 to 1.0]
    float distFromCenter = abs(v_TexCoord.y - 0.5) * 2.0;

    // 1. Blinding White-Hot Core Channel
    float core = exp(-distFromCenter * distFromCenter * 28.0);
    
    // 2. High-Voltage Electric Violet Inner Plasma Corona
    float corona = exp(-distFromCenter * distFromCenter * 6.0);
    
    // 3. Wide Soft Cyan Atmospheric Halo
    float halo = exp(-distFromCenter * 2.2);

    vec3 coreColor   = vec3(4.5, 4.5, 5.0);   // Blinding white-hot core
    vec3 coronaColor = vec3(0.85, 0.45, 1.40); // Deep electric violet plasma
    vec3 haloColor   = vec3(0.25, 0.70, 1.30); // Atmospheric cyan glow

    vec3 finalEmissive = (coreColor * core * 2.2 + coronaColor * corona * 1.3 + haloColor * halo * 0.75) * v_Intensity;

    // Micro-branch attenuation per subdivision level
    float branchFade = pow(0.72, v_Level);
    finalEmissive *= branchFade;

    float alpha = clamp((core * 1.0 + corona * 0.8 + halo * 0.4) * v_Intensity, 0.0, 1.0);
    FragColor = vec4(finalEmissive, alpha);
}
