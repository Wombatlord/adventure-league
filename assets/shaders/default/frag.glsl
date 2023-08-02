#version 330

uniform sampler2D scene;

in vec2 uv;
out vec4 rgba;

void main() {
    rgba = texture(scene, uv);
}
