#version 330
uniform vec3 line_color;
uniform float alpha;
out vec4 f_color;
void main() {
    f_color = vec4(line_color, alpha);
}