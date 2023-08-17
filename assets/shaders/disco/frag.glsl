#version 330
uniform sampler2D norm;
uniform sampler2D scene;
uniform float time;
uniform vec2 mouse;
in vec2 uv;
out vec4 rgba;
void main() {
    float s = sin(time);

    float c = cos(time);
    float radius = 2.;
    vec3 circ = radius*vec3(c, s, 0);
    vec3 offset = -1.*vec3(1.+2*mouse, 2.);
    vec3 light_loc = circ+offset;


    vec3 light = normalize(vec3(0.) - light_loc);
    vec4 normal = texture(norm, uv);
    vec3 light_col = vec3(c, s, (c-s)/2.)/2. + 0.5;
    vec3 illum = light_col*(dot(light, normal.xyz));

    rgba = vec4(texture(scene, uv).rgb*illum, 1.);
}
