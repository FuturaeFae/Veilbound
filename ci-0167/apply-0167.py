from pathlib import Path
import re
import shutil
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
ci = Path(__file__).resolve().parent

# Stage the 0.1.67 crystalline Core implementation over the exact validated 0.1.66 baseline.
copies = {
    'DimensionalCoreRenderer.java': 'src/main/java/dev/futurae/veilbound/client/render/DimensionalCoreRenderer.java',
    'DimensionalCoreRenderPipelines.java': 'src/main/java/dev/futurae/veilbound/client/render/DimensionalCoreRenderPipelines.java',
    'DimensionalCoreBlock.java': 'src/main/java/dev/futurae/veilbound/block/DimensionalCoreBlock.java',
    'dimensional_core.vsh': 'src/main/resources/assets/veilbound/shaders/core/dimensional_core.vsh',
    'dimensional_core.fsh': 'src/main/resources/assets/veilbound/shaders/core/dimensional_core.fsh',
    'DimensionalCoreVisualScaleSelfTest.java': 'src/test/java/dev/futurae/veilbound/block/DimensionalCoreVisualScaleSelfTest.java',
}
for src_name, dst_name in copies.items():
    src = ci / src_name
    dst = root / dst_name
    if not src.is_file():
        raise SystemExit(f'missing 0.1.67 replacement: {src_name}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)

props = root / 'gradle.properties'
text = props.read_text(encoding='utf-8')
if 'mod_version=0.1.66-dev' not in text:
    raise SystemExit('0.1.67 baseline is not exact 0.1.66-dev')
props.write_text(text.replace('mod_version=0.1.66-dev', 'mod_version=0.1.67-dev', 1), encoding='utf-8')

client = root / 'src/main/java/dev/futurae/veilbound/client/VeilboundClient.java'
text = client.read_text(encoding='utf-8')
import_line = 'import dev.futurae.veilbound.client.render.DimensionalCoreRenderPipelines;\n'
if import_line not in text:
    marker = 'import dev.futurae.veilbound.client.render.DimensionalCoreRenderer;\n'
    if marker not in text:
        raise SystemExit('could not locate Core renderer import')
    text = text.replace(marker, marker + import_line, 1)
registration = '        modBus.addListener(DimensionalCoreRenderPipelines::register);\n'
if registration not in text:
    marker = '        modBus.addListener(VeilBoundaryRenderPipeline::register);\n'
    if marker not in text:
        raise SystemExit('could not locate render-pipeline registration block')
    text = text.replace(marker, registration + marker, 1)
client.write_text(text, encoding='utf-8')

build = root / 'build.gradle'
text = build.read_text(encoding='utf-8')
marker = '// VEILBOUND_0167_CORE_VISUAL_SELF_TEST'
if marker not in text:
    text += '''

// VEILBOUND_0167_CORE_VISUAL_SELF_TEST
tasks.register('dimensionalCoreVisualScaleSelfTest', JavaExec) {
    dependsOn testClasses
    classpath = sourceSets.test.runtimeClasspath
    mainClass = 'dev.futurae.veilbound.block.DimensionalCoreVisualScaleSelfTest'
}
check.dependsOn tasks.named('dimensionalCoreVisualScaleSelfTest')
'''
build.write_text(text, encoding='utf-8')

# Terminal/Core interaction polish. This applies to the historical baseline before the final cleanup
# deletes all disconnected development-era feature clusters.
gui_patch = ci / 'gui-polish.patch'
if not gui_patch.is_file():
    raise SystemExit('missing 0.1.67 GUI polish patch')
subprocess.run(['patch', '-p1', '--batch', '-i', str(gui_patch)], cwd=root, check=True)

# Match the current ME-terminal interaction model more closely: left click withdraws a full stack,
# right click withdraws half a stack, while the server remains authoritative over the requested amount.
ae2_patch = ci / 'ae2-withdrawal-polish.patch'
if not ae2_patch.is_file():
    raise SystemExit('missing 0.1.67 AE-style withdrawal patch')
subprocess.run(['patch', '-p1', '--batch', '-i', str(ae2_patch)], cwd=root, check=True)

# Complete vanilla Matter coverage, persistent terminal mode, shared vanilla GUI styling, distinct
# resource animations/drops, adjacent Void Anchor placement, and the wispy Genesis Seed asset.
feature_pass = ci / 'apply-feature-pass.py'
if not feature_pass.is_file():
    raise SystemExit('missing 0.1.67 feature-pass applicator')
subprocess.run([sys.executable, str(feature_pass), str(root)], check=True)

# Verify the requested active feature changes before dead-source pruning.
terminal = root / 'src/main/java/dev/futurae/veilbound/client/screen/VeilInventoryScreen.java'
terminal_text = terminal.read_text(encoding='utf-8')
if 'ContainerInput.PICKUP' not in terminal_text or 'setTooltipForNextFrame(font, stack' not in terminal_text:
    raise SystemExit('Veil Inventory GUI polish did not apply')
if '(maxStack + 1) / 2' not in terminal_text:
    raise SystemExit('ME-style half-stack withdrawal polish did not apply')
if 'VeilInventoryPreferences.craftingMode()' not in terminal_text:
    raise SystemExit('persistent Veil Inventory mode did not apply')

server_terminal = root / 'src/main/java/dev/futurae/veilbound/platform/neoforge/inventory/NeoForgeVeilInventoryController.java'
if 'Math.min(payload.resource().getMaxStackSize(), Math.max(1, payload.quantity()))' not in server_terminal.read_text(encoding='utf-8'):
    raise SystemExit('server withdrawal quantity guard did not apply')

core_screen = root / 'src/main/java/dev/futurae/veilbound/client/screen/DomainControlsScreen.java'
if 'completely covered the tabs, expansion toggle, and six direction buttons' not in core_screen.read_text(encoding='utf-8'):
    raise SystemExit('Core control widget-layer fix did not apply')

# Remove null registry aliases, disconnected feature implementations, orphaned render resources and
# tests, and replace the old monument/lance collision supplement with a Core-only implementation.
cleanup = ci / 'cleanup-unused.py'
if not cleanup.is_file():
    raise SystemExit('missing deterministic unused-source cleanup')
subprocess.run([sys.executable, str(cleanup), str(root)], check=True)

# The deleted monument test used to be wired directly into check; remove its now-orphaned task.
text = build.read_text(encoding='utf-8')
text = re.sub(
    r"\ntasks\.register\('engineeringMonumentFieldSelfTest', JavaExec\) \{.*?\n\}\n\ncheck\.dependsOn tasks\.named\('engineeringMonumentFieldSelfTest'\)\n",
    '\n', text, flags=re.S)
build.write_text(text, encoding='utf-8')

# Strict second pass catches package-private helpers, removes the last unregistered Boundary Pylon
# branches, prunes dead translations, and verifies that all surviving resource/build hooks resolve.
final_cleanup = ci / 'cleanup-unused-final.py'
if not final_cleanup.is_file():
    raise SystemExit('missing strict final unused-source cleanup')
subprocess.run([sys.executable, str(final_cleanup), str(root)], check=True)

# Final source-tree audit. At this point old compatibility implementations must not exist anywhere in
# runtime source. Executed persistence/migration readers remain because they are live world-safety code.
java_root = root / 'src/main/java'
all_java = '\n'.join(path.read_text(encoding='utf-8', errors='ignore') for path in java_root.rglob('*.java'))
for forbidden in (
    'EngineeringMonumentBlock', 'EngineeringMonumentCollisionState', 'EngineeringMonumentRenderer',
    'VeilLanceBlock', 'VeilboundDataComponents', 'NeoForgeVeilInterfaceCapabilities',
    'BoundaryPylonBindingService', 'BreachLinkData', 'BOUNDARY_PYLON.get()',
    '@Deprecated public static final', 'VOID_ANCHOR_FLOOR'):
    if forbidden in all_java:
        raise SystemExit(f'0.1.67 cleanup audit failed: {forbidden}')

core_collision = root / 'src/main/java/dev/futurae/veilbound/block/DimensionalCoreCollisionState.java'
if not core_collision.is_file():
    raise SystemExit('Core-only oversized collision source missing after cleanup')
core_collision_text = core_collision.read_text(encoding='utf-8')
if 'VeilboundBlocks.DIMENSIONAL_CORE.get()' not in core_collision_text or 'VEIL_LANCE' in core_collision_text:
    raise SystemExit('Core-only collision cleanup is incomplete')

if 'engineeringMonumentFieldSelfTest' in build.read_text(encoding='utf-8'):
    raise SystemExit('orphaned engineering monument validation task remained')

print('VEILBOUND_0167_APPLY=PASS floating_crystal_core=staged material=physical_prismatic fragments=same_material levels=5 gui_polish=PASS core_buttons=PASS ae_withdrawal=PASS feature_polish=PASS unused_legacy=REMOVED')
