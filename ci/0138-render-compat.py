#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: 0138-render-compat.py <Veilbound source root>')
root = Path(sys.argv[1]).resolve()
p = root / 'src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderPipeline.java'
s = p.read_text()
replacements = [
    ('import com.mojang.blaze3d.pipeline.BlendFunction;\n', 'import com.mojang.blaze3d.PrimitiveTopology;\nimport com.mojang.blaze3d.pipeline.BlendFunction;\n'),
    ('import com.mojang.blaze3d.shaders.UniformType;\n', ''),
    ('import com.mojang.blaze3d.vertex.VertexFormat;\n', ''),
    ('import net.minecraft.client.renderer.rendertype.RenderSetup;\n', 'import net.minecraft.client.renderer.BindGroupLayouts;\nimport net.minecraft.client.renderer.rendertype.RenderSetup;\n'),
    ('            .withUniform("DynamicTransforms", UniformType.UNIFORM_BUFFER)\n            .withUniform("Projection", UniformType.UNIFORM_BUFFER)\n', '            .withBindGroupLayout(BindGroupLayouts.MATRICES_PROJECTION)\n'),
    ('            .withVertexFormat(DefaultVertexFormat.POSITION_TEX_COLOR, VertexFormat.Mode.QUADS)\n', '            .withVertexBinding(0, DefaultVertexFormat.POSITION_TEX_COLOR)\n            .withPrimitiveTopology(PrimitiveTopology.QUADS)\n'),
    ('                    .sortOnUpload()\n                    .bufferSize(RenderType.SMALL_BUFFER_SIZE)\n                    .createRenderSetup()', '                    .sortOnUpload()\n                    .createRenderSetup()'),
]
for old, new in replacements:
    if old not in s:
        raise SystemExit(f'Expected 26.1-style render pipeline source not found: {old!r}')
    s = s.replace(old, new)
p.write_text(s)
print('Applied Minecraft 26.2 render-pipeline compatibility fixes for Veil boundary')
