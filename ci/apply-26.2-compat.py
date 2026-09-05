#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: apply-26.2-compat.py <Veilbound source root>')
root = Path(sys.argv[1]).resolve()
java = root / 'src/main/java'
if not java.is_dir():
    raise SystemExit(f'Java source root not found: {java}')

# Minecraft 26.2 moved ServerPlayer feedback from displayClientMessage to sendSystemMessage.
changed = 0
for p in java.rglob('*.java'):
    s = p.read_text()
    n = s.count('.displayClientMessage(')
    if n:
        p.write_text(s.replace('.displayClientMessage(', '.sendSystemMessage('))
        changed += n
if changed != 99:
    raise SystemExit(f'Expected 99 ServerPlayer message API replacements, got {changed}')

# Camera render state moved into the level render-state package in 26.2.
p = java / 'dev/futurae/veilbound/client/render/ThresholdPortalRenderer.java'
s = p.read_text()
old = 'import net.minecraft.client.renderer.state.CameraRenderState;'
new = 'import net.minecraft.client.renderer.state.level.CameraRenderState;'
if old not in s:
    raise SystemExit('ThresholdPortalRenderer old CameraRenderState import not found')
p.write_text(s.replace(old, new))

# Screen now has protected rebuildWidgets(); let the inherited lifecycle implementation do the rebuild.
block = '    private void rebuildWidgets() {\n        clearWidgets();\n        init();\n    }\n\n'
for rel in [
    'dev/futurae/veilbound/client/screen/MemoryManagementScreen.java',
    'dev/futurae/veilbound/client/screen/VeilInventoryScreen.java',
]:
    p = java / rel
    s = p.read_text()
    if block not in s:
        raise SystemExit(f'Expected private rebuildWidgets helper not found: {rel}')
    p.write_text(s.replace(block, ''))

# JSpecify type-use annotation cannot be placed before a fully-qualified type in Java 25.
p = java / 'dev/futurae/veilbound/block/entity/VeilInterfaceBlockEntity.java'
s = p.read_text()
anchor = 'import dev.futurae.veilbound.matter.MatterTransmutationService;\n'
if anchor not in s:
    raise SystemExit('MatterTransmutationService import anchor missing')
s = s.replace(anchor, anchor + 'import dev.futurae.veilbound.matter.MatterTransmutationState;\n')
old = '@Nullable dev.futurae.veilbound.matter.MatterTransmutationState matterState,'
if old not in s:
    raise SystemExit('Qualified nullable MatterTransmutationState declaration missing')
s = s.replace(old, '@Nullable MatterTransmutationState matterState,')
p.write_text(s)

# BreakBlockEvent#getLevel is LevelAccessor in 26.2; target discovery only requires getBlockState.
p = java / 'dev/futurae/veilbound/platform/neoforge/NeoForgeVeilforgedEquipmentCoordinator.java'
s = p.read_text()
old = 'net.minecraft.world.level.Level level,'
count = s.count(old)
if count != 3:
    raise SystemExit(f'Expected 3 target helper Level parameters, got {count}')
p.write_text(s.replace(old, 'net.minecraft.world.level.LevelAccessor level,'))

print('Applied Minecraft/NeoForge 26.2 compatibility pass 1')

# Second compile pass: current 26.2 server/registry accessors plus two internal record accessor typos.
replacements = {
    'dev/futurae/veilbound/platform/neoforge/threshold/NeoForgeThresholdDeactivationCoordinator.java': [
        ('breaker.getServer()', 'breaker.level().getServer()'),
    ],
    'dev/futurae/veilbound/platform/neoforge/threshold/NeoForgeThresholdPortalTransit.java': [
        ('player.getServer()', 'player.level().getServer()'),
    ],
    'dev/futurae/veilbound/platform/neoforge/NeoForgeMemoryManagementController.java': [
        ('definition.prerequisites()', 'definition.prerequisiteMemoryIds()'),
    ],
    'dev/futurae/veilbound/platform/neoforge/NeoForgeProjectEMatterSeeder.java': [
        ('holder.key().identifier().toString()', 'holder.getRegisteredName()'),
    ],
    'dev/futurae/veilbound/block/entity/OntologicalHarvesterBlockEntity.java': [
        ('plan.potentialProduced()', 'plan.potential()'),
    ],
    'dev/futurae/veilbound/platform/neoforge/world/VeilboundDomainLevelData.java': [
        ('server.overworld().getLevelData());', '(net.minecraft.world.level.storage.ServerLevelData) server.overworld().getLevelData());'),
    ],
}
for rel, pairs in replacements.items():
    p = java / rel
    s = p.read_text()
    for old, new in pairs:
        if old not in s:
            raise SystemExit(f'Expected pass-2 source not found in {rel}: {old}')
        s = s.replace(old, new)
    p.write_text(s)

print('Applied Minecraft/NeoForge 26.2 compatibility pass 2')

# The Gradle test source set references Minecraft classes in DefinitionPathSelfTest.
# ModDevGradle only attaches its modding dependencies to additional source sets when requested.
build = root / 'build.gradle'
s = build.read_text()
anchor = '''    mods {
        veilbound {
            sourceSet sourceSets.main
        }
    }
'''
replacement = anchor + '''
    addModdingDependenciesTo sourceSets.test
'''
if anchor not in s:
    raise SystemExit('build.gradle mods anchor missing for test modding dependencies')
if 'addModdingDependenciesTo sourceSets.test' not in s:
    s = s.replace(anchor, replacement)
build.write_text(s)
print('Attached Minecraft/NeoForge modding dependencies to the test source set')
