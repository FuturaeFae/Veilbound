#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: 0146-fog-performance.py <source-root>')
root = Path(sys.argv[1]).resolve()

# Version
p = root / 'gradle.properties'
s = p.read_text()
if 'mod_version=0.1.45-dev' not in s:
    raise SystemExit('Expected 0.1.45-dev version marker not found')
p.write_text(s.replace('mod_version=0.1.45-dev', 'mod_version=0.1.46-dev', 1))

# Halve physical slices while preserving the old 32-slice optical density in the fragment shader.
p = root / 'src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderer.java'
s = p.read_text()
if 'private static final int FOG_LAYERS = 32;' not in s:
    raise SystemExit('Expected 0.1.45 fog layer count not found')
s = s.replace('private static final int FOG_LAYERS = 32;', 'private static final int FOG_LAYERS = 16;', 1)
p.write_text(s)

# Keep the same broad/billow/curl formula, but remove only the tiny fifth octave from each FBM.
# Then make every surviving slice optically equivalent to a pair of 0.1.45 slices.
p = root / 'src/main/resources/assets/veilbound/shaders/core/veil_boundary_fog.fsh'
s = p.read_text()
if 'for (int i = 0; i < 5; ++i)' not in s:
    raise SystemExit('Expected 0.1.45 five-octave FBM loop not found')
s = s.replace('for (int i = 0; i < 5; ++i)', 'for (int i = 0; i < 4; ++i)', 1)
old = '''    float alpha = fogColor.a * shape;\n    alpha = clamp(alpha, 0.012, 0.19);\n'''
new = '''    // 0.1.46 renders half as many spatial slices. Preserve the accumulated optical density of\n    // 0.1.45 by making each new slice equivalent to two old alpha-composited slices:\n    //   a_pair = 1 - (1 - a)^2\n    // This halves translucent overdraw without simply making the fog thinner.\n    float sourceAlpha = clamp(fogColor.a * shape, 0.012, 0.19);\n    float alpha = 1.0 - (1.0 - sourceAlpha) * (1.0 - sourceAlpha);\n'''
if old not in s:
    raise SystemExit('Expected 0.1.45 fog alpha block not found')
s = s.replace(old, new, 1)
p.write_text(s)

# Documentation
p = root / 'README.md'
s = p.read_text()
marker = '## 0.1.46-dev — Boundary fog performance pass\n'
if marker not in s:
    s += '''\n\n## 0.1.46-dev — Boundary fog performance pass\n\n- Preserves the 0.1.45 completely black wall, dense 1–3 block fog volume, uniform six-wall strength, 0.10-block edge overlap, and one-block camera-clear pocket.\n- Reduces spatial fog slices from 32 to 16, cutting translucent geometry and fragment overdraw in half. Each new slice uses optical alpha compensation (`1 - (1-a)^2`) so its accumulated density matches the paired 0.1.45 slices rather than looking thinner.\n- Reduces each FBM evaluation from five octaves to four. The removed fifth octave contributed only a very small high-frequency amplitude, while reducing procedural-noise work on every fog fragment.\n- No distance fade, wall-color change, cloud behavior change, collision change, or environment-progression change is introduced.\n'''
p.write_text(s)

print('Applied 0.1.46 boundary fog performance optimization')
