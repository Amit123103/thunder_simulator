#version 330 core

in vec2 v_TexCoord;
in float v_Level;
in float v_Intensity;

out vec4 FragColor;

void main()
{
    // Distance from central axis of lightning ribbon [0.0 to 1.0]
    float distFromCenter = abs(v_TexCoord.y - 0.5) * 2.0;

    // Core white-hot electric channel + outer cyan/violet plasma halo
    float core = exp(-distFromCenter * distFromCenter * 14.0);
    float halo = exp(-distFromCenter * 2.5);

    vec3 coreColor = vec3(3.5, 3.5, 4.0); // Blinding white core
    vec3 haloColor = vec3(0.35, 0.65, 1.2); // Electric cyan plasma aura

    vec3 finalEmissive = (coreColor * core * 1.5 + haloColor * halo * 0.8) * v_Intensity;

    // Attenuate micro-branches slightly
    float branchFade = pow(0.7, v_Level);
    finalEmissive *= branchFade;

    float alpha = clamp(halo * v_Intensity, 0.0, 1.0);
    FragColor = vec4(finalEmissive, alpha);
}
