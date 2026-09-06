#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: 0147-fog-detail-noise.py <source-root>')
root = Path(sys.argv[1]).resolve()

# Version
p = root / 'gradle.properties'
s = p.read_text()
if 'mod_version=0.1.46-dev' not in s:
    raise SystemExit('Expected 0.1.46-dev version marker not found')
p.write_text(s.replace('mod_version=0.1.46-dev', 'mod_version=0.1.47-dev', 1))

# Add one inexpensive, continuously-interpolated high-frequency world-space noise sample.
# This decorrelates the 16 retained fog slices and hides visible stepping without restoring the
# expensive 32-slice overdraw. It is world anchored, so player/camera motion cannot make it swim.
p = root / 'src/main/resources/assets/veilbound/shaders/core/veil_boundary_fog.fsh'
s = p.read_text()
old = '''    float smoke = broad * 0.54 + billow * 0.32 + curl * 0.14;\n    smoke = smoothstep(0.24, 0.77, smoke);\n\n    // The first block is intentionally a heavy bank. Layers through blocks two and three become\n'''
new = '''    float smoke = broad * 0.54 + billow * 0.32 + curl * 0.14;\n    smoke = smoothstep(0.24, 0.77, smoke);\n\n    // One extra smooth high-frequency value-noise sample breaks up the remaining 16 slice planes\n    // without bringing back 0.1.45's expensive layer count. Depth is folded into the coordinates\n    // so adjacent slices do not share the same fine pattern. This is entirely world-space anchored:\n    // camera/player movement never changes the sampled field.\n    vec3 detailCoord = fogWorldPos * 1.92\n            + vec3(depth01 * 13.71, depth01 * -9.43, depth01 * 17.29)\n            + drift * 0.18;\n    float detailNoise = noise3(detailCoord);\n    float detailSigned = detailNoise - 0.5;\n\n    // The first block is intentionally a heavy bank. Layers through blocks two and three become\n'''
if old not in s:
    raise SystemExit('Expected 0.1.46 smoke block not found')
s = s.replace(old, new, 1)

old = '''    float shape = mix(0.50 + smoke * 0.50, 0.15 + smoke * 0.85, tail);\n    shape = max(shape, denseCore * (0.78 + smoke * 0.22));\n\n    // 0.1.46 renders half as many spatial slices. Preserve the accumulated optical density of\n'''
new = '''    float shape = mix(0.50 + smoke * 0.50, 0.15 + smoke * 0.85, tail);\n    shape = max(shape, denseCore * (0.78 + smoke * 0.22));\n\n    // Fine density dither softens planar banding and pixel-like transitions while keeping the\n    // overall optical mass essentially unchanged. The dense first block gets a gentler modulation\n    // so it remains a nearly solid fog bank rather than becoming grainy.\n    float detailStrength = mix(0.055, 0.14, 1.0 - denseCore);\n    shape = clamp(shape * (1.0 + detailSigned * detailStrength)\n            + detailSigned * detailStrength * 0.22, 0.0, 1.15);\n\n    // 0.1.46 renders half as many spatial slices. Preserve the accumulated optical density of\n'''
if old not in s:
    raise SystemExit('Expected 0.1.46 shape block not found')
s = s.replace(old, new, 1)

old = '''    float grey = 0.075 + smoke * 0.105 + denseCore * 0.025;\n    vec3 color = vec3(grey);\n'''
new = '''    float grey = 0.075 + smoke * 0.105 + denseCore * 0.025;\n    // Tiny luminance variation makes the extra density detail readable without introducing color.\n    grey += detailSigned * 0.010 * (1.0 - denseCore * 0.65);\n    vec3 color = vec3(grey);\n'''
if old not in s:
    raise SystemExit('Expected 0.1.46 grey block not found')
s = s.replace(old, new, 1)
p.write_text(s)

# Documentation
p = root / 'README.md'
s = p.read_text()
marker = '## 0.1.47-dev — Fog detail-noise anti-banding pass\n'
if marker not in s:
    s += '''\n\n## 0.1.47-dev — Fog detail-noise anti-banding pass\n\n- Preserves the optimized 16-slice 0.1.46 fog, 1–3 block depth, optical-density compensation, pure-black shell, uniform six-wall strength, one-block camera-clear pocket, and 0.10-block edge overlap.\n- Adds one continuously interpolated high-frequency world-space value-noise sample per fog fragment. It decorrelates adjacent depth slices and breaks up planar/pixel-like banding without restoring the expensive 32-layer overdraw.\n- Fine density modulation is intentionally weaker in the dense first block and stronger in the rolling 2–3 block tail, keeping the near-wall bank thick while making the outer volume look smoother and more organic.\n- The detail field is anchored to world/Domain coordinates and only follows the existing slow time drift; player/camera movement is not part of its coordinate input.\n- Fog remains neutral charcoal/ash with no violet or blue tint.\n'''
p.write_text(s)

print('Applied 0.1.47 fog detail-noise anti-banding pass')
