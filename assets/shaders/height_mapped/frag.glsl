#version 330
uniform sampler2D norm;
uniform sampler2D scene;
uniform sampler2D height;
uniform sampler2D terrain;

uniform float scene_toggle;
uniform float height_toggle;
uniform float normal_toggle;
uniform float axes_toggle;
uniform float ray_toggle;
uniform float terrain_toggle;

uniform vec4 pt_col;
uniform vec3 pt_src;

uniform vec4 directional_col;
uniform vec3 directional_dir;

uniform vec4 ambient_col;

uniform vec3 light_balance;

uniform float time_since_start;

uniform mat4 transform;
in vec2 uv;
in vec2 xy;

out vec4 rgba;

vec2 to_world(vec2 screen) {
    return (transform * vec4(screen, 0.0, 1.0)).xy;
}

vec2 to_screen(vec3 world) {
    return (inverse(transform) * vec4(world, 1.0)).xy;
}

float sample_height(vec2 pt) {
    return  (texture(height, pt).z)*32.0-1.0;
}

vec4 draw_axes(vec4 in_col, vec3 px, vec3 fixed_pt) {
    float weight = 0.04;
    vec4 col = vec4(0.);
    float yz_plane = step(distance(px.x, fixed_pt.x), weight);
    col.r += yz_plane;

    float xz_plane = step(distance(px.y, fixed_pt.y), weight);
    col.g += xz_plane;

    float xy_plane = step(distance(px.z, fixed_pt.z), weight);
    col.b += xy_plane;
    return col;
}

vec3 get_surface_pt(vec2 screen_pt, vec2 world_pt) {
    float z = sample_height(screen_pt);
    vec3 xyz = vec3(world_pt-(z-.5)*vec2(1.), z);
    return xyz;
}

float on_off(float start, float stop, float x) {
    return step(start, x) * (1.-step(stop, x));
}

float depth_sample(vec2 world) {
    return float(texture(terrain, (world+.55)/10.))*32.0-1.0;
}

float cast_ray(vec3 ray, float time) {
    float flicker = 1.;
    flicker += 0.05*sin(1.*time);
    flicker += 0.035*cos(-(3./7.)*time)*cos(3.*(time+1.));
    flicker += 0.02*cos(-(3./11.)*time-1.)*cos(5.*(time+2.));

    float intensity = flicker*4.0/pow(0.6+length(ray), 2);
    float opacity = 10.;
    int iterations = 100;
    float sample_separation = length(ray)/float(iterations);
    vec3 direction = normalize(ray);
    float attenuation_per_sample = opacity*sample_separation;

    for (float i = 0.0; i < length(ray); i+=sample_separation) {
        vec3 sample_pt = pt_src + i * direction;
        float depth = (depth_sample(sample_pt.xy) - sample_pt.z);

        float attentuation = step(0.0, depth)*attenuation_per_sample;
        intensity *= (1.-attentuation);
    }

    intensity = log(intensity+1.);
    return intensity;
}

void main() {
    float z = sample_height(uv);
    vec3 xyz = get_surface_pt(uv, xy);

    vec3 ray = xyz - pt_src;

    float time = 10.*time_since_start;
    vec3 surface_normal = normalize(texture(norm, uv).xyz) * vec3(1., 1., 1.);

    float pt_intensity = cast_ray(ray, time);
    vec4 pt_diffuse = pt_intensity*pt_col*clamp(0.0, 1.0, dot(normalize(ray), -surface_normal));

    vec4 dir_diffuse = directional_col*dot(directional_dir, surface_normal);

    vec3 balance = normalize(light_balance);

    vec4 scene_col = texture(scene, uv);
    vec4 colour = vec4(0.);
    colour += ambient_col*scene_col*balance.x;
    colour += dir_diffuse*scene_col*balance.y;
    colour += pt_diffuse*scene_col*balance.z;

    vec4 final = vec4(0.);
    final += colour * scene_toggle;
    final += draw_axes(colour, xyz, vec3(0)) * axes_toggle;
    final += vec4(surface_normal, 1.) * normal_toggle;
    float d_sample = depth_sample(xyz.xy);
    final += vec4(xyz.xy/10, step(0.5,d_sample)*xyz.z+depth_sample(xyz.xy), 1.) * height_toggle;
    final += vec4(pt_intensity*normalize(ray)/2. + .5, 1.) * ray_toggle;
    final += texture(terrain, xyz.xy) * terrain_toggle;

    rgba = final;
}

