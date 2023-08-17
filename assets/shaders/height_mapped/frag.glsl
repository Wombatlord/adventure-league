#version 330
uniform sampler2D norm;
uniform sampler2D scene;
uniform sampler2D height;
uniform mat4 transform;
uniform vec2 mouse;


in vec2 uv;
in vec2 xy;

out vec4 rgba;

vec2 to_world(vec2 screen) {
    return (transform * vec4(screen, 0.0, 1.0)).xy;
}

float sample_height(vec2 xy) {
    return texture(
        height,
        (inverse(transform) * vec4(xy, 0.0, 1.0)).xy
    ).r*255.0;
}

void main() {
    vec3 light_loc = vec3(to_world(mouse), 20.0);
    vec4 light_colour = vec4(0.8, 0.6, 0.2, 1.0).rgba;
    vec3 xyz = vec3(xy, sample_height(xy));
    vec3 ray = xyz - light_loc;
    vec3 surface_normal = normalize(texture(norm, uv).xyz);
    vec3 ambient_dir = normalize(vec3(1.0, 2.0, 2.0));

    float intensity = 150.0/pow(1.0+length(ray), 2);
    float opacity = 0.05;

    for (int i = 0; i < 100; i++) {
        vec3 sample_pt = float(i)/100.0 * ray + light_loc;
        float depth = (sample_height(sample_pt.xy) - sample_pt.z);

        float attentuation = step(0.0, depth)*opacity;
        intensity -= attentuation;
    }

    intensity = clamp(intensity, 0.0, 1.0) ;


    vec4 diffuse_light_colour = light_colour*clamp(0.0, 1.0, dot(normalize(ray), -surface_normal));
    float ambient = dot(ambient_dir, surface_normal);
    vec4 scene_col = texture(scene, uv);

    vec4 col = vec4(0.0);
    col += 0.5*diffuse_light_colour*intensity*scene_col;
    col += 0.5*ambient*scene_col;

    rgba = col;
}

