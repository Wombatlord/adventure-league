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
uniform float terrain_transparency;

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
    return (texture(height, pt).z)*32.0-1.0;
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

vec3 get_los() {
    return normalize((transform*vec4(0.0, 0.0, -10.0, 0.0)).xyz);
}

vec3 get_surface_pt(vec2 screen_pt, vec2 world_pt) {
    float z = sample_height(screen_pt);
    vec3 xy0 = vec3(world_pt, 0.0);
    vec3 los = sqrt(3.) * get_los();
    vec3 adj = 0.5*vec3(los.xy, 0.0);

    vec3 xyz = xy0 + adj - vec3(z*los.xy, 0) + vec3(0., 0., z);
    return xyz;
}

float on_off(float start, float stop, float x) {
    return step(start, x) * (1.-step(stop, x));
}

float depth_sample(vec2 world) {
    vec2 adj = vec2(.5); // for some reason this one needs to be constant under rotation
    return float(texture(terrain, (world+adj)/10.))*32.0-1.0;
}

float flicker(float t) {
    float flicker = 1.;
    flicker += 0.05*sin(1.*t);
    flicker += 0.035*cos(-(3./7.)*t)*cos(3.*(t+1.));
    flicker += 0.02*cos(-(3./11.)*t-1.)*cos(5.*(t+2.));
    return flicker;
}

float cast_ray(vec3 ray, float time) {
    float flicker_f = flicker(time);

    float intensity = flicker_f*4.0/pow(0.6+length(ray), 2);
    int iterations = 150;
    float sample_separation = length(ray)/float(iterations);
    vec3 direction = normalize(ray);
    float transmission_per_sample = pow(terrain_transparency, sample_separation);
    float no_occlusion = 1.;

    for (float i = 0.0; i < length(ray); i+=sample_separation) {
        vec3 sample_pt = pt_src + i * direction;
        float depth = (depth_sample(sample_pt.xy) - sample_pt.z);

        float transmission_factor = mix(no_occlusion, transmission_per_sample, step(0.0, depth));
        intensity *= transmission_factor;
    }

    return intensity;
}

float band(float center, float width, float x) {
    return step(center-width/2., x)*(1.-step(center+width/2, x));
}

vec3 rotate_normals(vec3 normals) {
    vec3 los = get_los();
    vec3 basis3 = vec3(0., 0., 1.);
    vec3 planar1 = normalize(cross(basis3, vec3(los.xy, 0.0)));
    vec3 planar0 = -cross(basis3, planar1);
    vec3 basis0 = normalize(planar0 - planar1);
    vec3 basis1 = normalize(planar0 + planar1);

    return normals.x*basis0 + normals.y*basis1 + normals.z*basis3;
}

void main() {
    float z = sample_height(uv);
    vec3 xyz = get_surface_pt(uv, xy);

    vec3 ray = xyz - pt_src;

    float time = 10.*time_since_start;
    vec3 surface_normal = rotate_normals(normalize(texture(norm, uv).xyz));

    float pt_intensity = cast_ray(ray, time);
    vec4 pt_diffuse = pt_intensity*pt_col*abs(dot(normalize(ray), -surface_normal));

    vec4 dir_diffuse = directional_col*clamp(dot(directional_dir, -surface_normal), 0.0, 1.0);
    vec3 balance = light_balance;

    vec4 scene_col = texture(scene, uv);
    vec4 colour = vec4(0.);
    colour += ambient_col*scene_col*balance.x;
    colour += dir_diffuse*scene_col*balance.y;
    colour += pt_diffuse*scene_col*balance.z;

    vec4 final = vec4(0.);
    final += colour * scene_toggle;
    final += draw_axes(colour, xyz, vec3(0)) * axes_toggle;
    final += vec4(0.5 + 0.5*surface_normal, 1.) * normal_toggle;

    vec3 pt = fract(get_surface_pt(uv,xy));
    final += height_toggle * (vec4(
        band(0.5, 0.05, fract(pt).x),
        band(0.5, 0.05, fract(pt).y),
        0,
        1.
    ) + vec4(xyz, 0.0)*vec4(0.1,0.1,1.0,1.0));

    final += vec4(pt_intensity*vec3(abs(dot(normalize(ray), -surface_normal))), 1.) * ray_toggle;
    final += texture(terrain, xyz.xy) * terrain_toggle;

    rgba = final;
}

