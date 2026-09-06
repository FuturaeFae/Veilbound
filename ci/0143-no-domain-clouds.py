#!/usr/bin/env python3
from pathlib import Path
import json
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: 0143-no-domain-clouds.py <source-root>')
root = Path(sys.argv[1]).resolve()

# Version
p = root / 'gradle.properties'
s = p.read_text()
if 'mod_version=0.1.42-dev' not in s:
    raise SystemExit('Expected 0.1.42-dev version marker not found')
p.write_text(s.replace('mod_version=0.1.42-dev', 'mod_version=0.1.43-dev', 1))

# Client no-op cloud renderer. Returning true is NeoForge 26.2's contract for suppressing vanilla clouds.
p = root / 'src/main/java/dev/futurae/veilbound/client/render/NoDomainCloudsRenderer.java'
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text('''package dev.futurae.veilbound.client.render;\n\nimport net.minecraft.client.CloudStatus;\nimport net.minecraft.client.renderer.state.level.LevelRenderState;\nimport net.minecraft.world.phys.Vec3;\nimport net.neoforged.neoforge.client.CustomCloudsRenderer;\nimport org.joml.Matrix4fc;\n\n/**\n * Permanently suppresses Minecraft's vanilla cloud sheet inside every Veilbound personal Domain.\n *\n * <p>Clouds are intentionally not a Memory/environment toggle. Open Sky, Celestial Cycle, Gentle\n * Rain, environmental zones, or future Domain upgrades may provide sky/weather state, but they\n * cannot restore the global vanilla cloud layer. Any future cloud-like visuals must be explicitly\n * Domain-local effects owned by Veilbound.</p>\n */\npublic final class NoDomainCloudsRenderer implements CustomCloudsRenderer {\n    @Override\n    public boolean renderClouds(\n            LevelRenderState levelRenderState,\n            Vec3 camPos,\n            CloudStatus cloudStatus,\n            int cloudColor,\n            float cloudHeight,\n            int cloudRange,\n            Matrix4fc modelViewMatrix) {\n        return true;\n    }\n}\n''')

# Register the renderer alongside the Domain sky gate.
p = root / 'src/main/java/dev/futurae/veilbound/client/VeilboundClient.java'
s = p.read_text()
if 'NoDomainCloudsRenderer' not in s:
    s = s.replace(
        'import dev.futurae.veilbound.client.render.MemorySkyboxGateRenderer;\n',
        'import dev.futurae.veilbound.client.render.MemorySkyboxGateRenderer;\nimport dev.futurae.veilbound.client.render.NoDomainCloudsRenderer;\n',
        1)
needle = '''        event.registerSkyboxRenderer(\n                Identifier.fromNamespaceAndPath(Veilbound.MOD_ID, "memory_sky_gate"),\n                new MemorySkyboxGateRenderer());\n'''
replacement = needle + '''        event.registerCloudRenderer(\n                Identifier.fromNamespaceAndPath(Veilbound.MOD_ID, "no_clouds"),\n                new NoDomainCloudsRenderer());\n'''
if 'new NoDomainCloudsRenderer()' not in s:
    if needle not in s:
        raise SystemExit('Expected Domain sky renderer registration not found')
    s = s.replace(needle, replacement, 1)
p.write_text(s)

# Make the shared Domain dimension select the suppressing renderer for all owners and all Memories.
p = root / 'src/main/resources/data/veilbound/dimension_type/domain.json'
data = json.loads(p.read_text())
attrs = data.setdefault('attributes', {})
attrs['neoforge:custom_clouds'] = 'veilbound:no_clouds'
p.write_text(json.dumps(data, indent=2) + '\n')

# Documentation marker for the authoritative behavior.
p = root / 'README.md'
s = p.read_text()
marker = '## 0.1.43-dev — Domain cloud suppression\n'
if marker not in s:
    s += '''\n\n## 0.1.43-dev — Domain cloud suppression\n\n- Vanilla Minecraft clouds are permanently suppressed inside every personal Domain through the NeoForge 26.2 custom-cloud renderer hook.\n- This is independent of Domain size and independent of Memories: Open Sky, Celestial Cycle, Gentle Rain, Environmental Zones, and future environment upgrades do not restore the global vanilla cloud sheet.\n- Gentle Rain may still provide Domain-local rain/overcast ambience. Any future visible cloud structures must be explicitly Veilbound-owned Domain-local effects rather than vanilla world clouds.\n'''
p.write_text(s)

print('Applied 0.1.43 permanent no-cloud Domain rendering rule')
