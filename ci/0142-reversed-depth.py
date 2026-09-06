#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: 0142-reversed-depth.py <source-root>')

root = Path(sys.argv[1]).resolve()

props = root / 'gradle.properties'
s = props.read_text()
if 'mod_version=0.1.41-dev' not in s:
    raise SystemExit('Expected 0.1.41 version marker not found')
props.write_text(s.replace('mod_version=0.1.41-dev', 'mod_version=0.1.42-dev', 1))

pipeline = root / 'src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderPipeline.java'
s = pipeline.read_text()
old = 'new DepthStencilState(CompareOp.LESS_THAN_OR_EQUAL, false, 0.0F, 0.0F)'
new = 'new DepthStencilState(CompareOp.GREATER_THAN_OR_EQUAL, false, 0.0F, 0.0F)'
if old not in s:
    raise SystemExit('Expected legacy Veil depth comparison not found')
pipeline.write_text(s.replace(old, new, 1))

print('Applied 0.1.42 reversed-Z Veil boundary depth comparison')
