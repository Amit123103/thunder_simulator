#version 330 core

in vec2 v_UV;
in float v_Type;
in vec4 v_Color;
in float v_LifeRatio;

out vec4 FragColor;

void main()
{
    vec2 center = v_UV - vec2(0.5);
    float distSq = dot(center, center);

    // Particle Type 0: SPARK
    if (v_Type == 0.0)
    {
        if (distSq > 0.25) discard;
        float glow = exp(-distSq * 16.0);
        vec3 emissiveSpark = v_Color.rgb * glow * 6.0;
        FragColor = vec4(emissiveSpark, glow * v_LifeRatio);
    }
    // Particle Type 1: SMOKE
    else if (v_Type == 1.0)
    {
        if (distSq > 0.25) discard;
        float alpha = (1.0 - smoothstep(0.0, 0.25, distSq)) * v_Color.a * v_LifeRatio;
        FragColor = vec4(v_Color.rgb, alpha * 0.4);
    }
    // Particle Type 2: ROCK DEBRIS
    else if (v_Type == 2.0)
    {
        if (distSq > 0.22) discard;
        FragColor = vec4(v_Color.rgb * (0.8 + 0.2 * sin(v_UV.x * 20.0)), 1.0);
    }
    // Particle Type 3: RAIN STREAK
    else
    {
        float alpha = (1.0 - abs(v_UV.x - 0.5) * 2.0) * 0.35;
        FragColor = vec4(v_Color.rgb, alpha);
    }
}
