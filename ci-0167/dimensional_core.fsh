#version 330

in vec4 vertexColor;
in vec2 materialUv;
out vec4 fragColor;

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float valueNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash21(i);
    float b = hash21(i + vec2(1.0, 0.0));
    float c = hash21(i + vec2(0.0, 1.0));
    float d = hash21(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float sum = 0.0;
    float amp = 0.55;
    mat2 rot = mat2(0.80, -0.60, 0.60, 0.80);
    for (int i = 0; i < 4; ++i) {
        sum += valueNoise(p) * amp;
        p = rot * p * 2.03 + vec2(7.17, 13.41);
        amp *= 0.50;
    }
    return sum;
}

vec3 prism(float phase) {
    return 0.56 + 0.44 * cos(6.2831853 * (phase + vec3(0.00, 0.31, 0.67)));
}

void main() {
    vec2 uv = materialUv;

    if (vertexColor.a >= 0.985) {
        float depth = fbm(uv * 2.6 + vec2(1.7, 4.1));
        float cloud = fbm(uv * 6.2 + vec2(9.3, 2.8));
        float micro = valueNoise(uv * 34.0 + vec2(3.8, 17.2));

        float f1 = abs(sin((uv.x * 8.6 + uv.y * 3.7 + depth * 2.1) * 3.1415926));
        float f2 = abs(sin((uv.x * -4.1 + uv.y * 10.9 + cloud * 1.8) * 3.1415926));
        float f3 = abs(sin((uv.x * 13.3 - uv.y * 6.4 + micro * 1.1) * 3.1415926));
        float fracture = 1.0 - smoothstep(0.020, 0.075, min(f1, min(f2, f3)));

        vec2 cellUv = uv * vec2(4.7, 5.9);
        vec2 cell = abs(fract(cellUv) - 0.5);
        float edge = 1.0 - smoothstep(0.34, 0.49, max(cell.x, cell.y));
        float facetSeed = hash21(floor(cellUv));
        float facetShade = mix(0.72, 1.20, facetSeed) * mix(0.82, 1.08, edge);

        float spectralPhase = fract(uv.x * 0.37 + uv.y * 0.23 + depth * 0.82 + cloud * 0.19);
        vec3 spectral = prism(spectralPhase);
        vec3 deepColor = vertexColor.rgb * (0.48 + depth * 0.58);
        vec3 mineral = mix(deepColor, spectral, 0.11 + 0.15 * cloud);

        float pocket = smoothstep(0.18, 0.72, depth * (0.65 + cloud * 0.55));
        mineral *= mix(0.58, 1.08, pocket) * facetShade;
        mineral += fracture * mix(vec3(0.34, 0.20, 0.70), vec3(0.72, 0.84, 1.00), cloud) * 0.72;

        float glint = smoothstep(0.958, 0.995, micro + facetSeed * 0.22);
        mineral += glint * mix(vec3(0.32, 0.64, 1.00), vec3(1.00, 0.58, 0.96), spectralPhase) * 0.72;

        fragColor = vec4(max(mineral, vec3(0.0)), 1.0);
    } else {
        float bloomNoise = fbm(uv * 4.3 + vec2(5.2, 11.8));
        float veins = 1.0 - smoothstep(0.03, 0.18,
                abs(sin((uv.x * 7.1 - uv.y * 8.4 + bloomNoise * 1.7) * 3.1415926)));
        vec3 c = vertexColor.rgb * (1.05 + bloomNoise * 0.62);
        c += veins * vec3(0.55, 0.36, 1.00) * 0.42;
        fragColor = vec4(c, vertexColor.a * (0.80 + 0.20 * bloomNoise));
    }
}
