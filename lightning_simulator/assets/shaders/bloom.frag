#version 330 core

in vec2 v_TexCoord;

uniform sampler2D u_Texture;
uniform float u_Threshold;
uniform vec2 u_TexelSize;
uniform int u_Pass; // 0 = Threshold Extract, 1 = Kawase Blur

out vec4 FragColor;

void main()
{
    if (u_Pass == 0)
    {
        // Threshold Extraction Pass
        vec3 color = texture(u_Texture, v_TexCoord).rgb;
        float brightness = dot(color, vec3(0.2126, 0.7152, 0.0722));
        if (brightness > u_Threshold)
        {
            FragColor = vec4(color, 1.0);
        }
        else
        {
            FragColor = vec4(0.0, 0.0, 0.0, 1.0);
        }
    }
    else
    {
        // 5-Tap Kawase Blur Box Filter
        vec2 off = u_TexelSize * 1.5;
        vec3 sum = texture(u_Texture, v_TexCoord).rgb * 4.0;
        sum += texture(u_Texture, v_TexCoord + vec2(-off.x, -off.y)).rgb;
        sum += texture(u_Texture, v_TexCoord + vec2( off.x, -off.y)).rgb;
        sum += texture(u_Texture, v_TexCoord + vec2(-off.x,  off.y)).rgb;
        sum += texture(u_Texture, v_TexCoord + vec2( off.x,  off.y)).rgb;

        FragColor = vec4(sum / 8.0, 1.0);
    }
}
