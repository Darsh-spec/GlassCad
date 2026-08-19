#version 330
in vec3 v_color;
in float v_alpha;
out vec4 f_color;
void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    if (dist > 0.5) discard;
    float glow = smoothstep(0.5, 0.0, dist);
    f_color = vec4(v_color * glow, v_alpha * glow);
}