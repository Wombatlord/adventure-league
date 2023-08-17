#version 330
            
in vec2 in_vert;
in vec2 in_uv;

uniform mat4 transform;

out vec2 uv;
out vec2 xy;

void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);
    uv = in_uv;
    xy = (transform * vec4(in_uv, 0., 1.)).xy;
}
