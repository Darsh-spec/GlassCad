#version 330
in vec3 in_position;
in vec3 in_color;
uniform mat4 mvp;
uniform float point_size;
uniform float alpha;
out vec3 v_color;
out float v_alpha;
void main() {
    gl_Position = mvp * vec4(in_position, 1.0);
    gl_PointSize = point_size;
    v_color = in_color;
    v_alpha = alpha;
}