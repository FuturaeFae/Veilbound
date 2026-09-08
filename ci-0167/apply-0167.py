from pathlib import Path
import shutil, subprocess, sys

root = Path(sys.argv[1]).resolve()
ci = Path(__file__).resolve().parent

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

# 0.1.67 hotfix: first-release engineering monuments were intentionally removed in 0.1.66,
# leaving their deprecated DeferredBlock holders null. Legacy collision/interaction code must never
# dereference those null holders while normal worlds are loading or blocks are being clicked.
monument = root / 'src/main/java/dev/futurae/veilbound/block/EngineeringMonumentBlock.java'
text = monument.read_text(encoding='utf-8')
helper_marker = '    /** Detailed local collision boxes used by the out-of-cell collision supplement. */\n'
helper = '''    private static boolean legacyRegistrationsAvailable() {
        return VeilboundBlocks.CHRONAL_ENGINE_BLOCK != null
                && VeilboundBlocks.MNEMONIC_NEXUS_BLOCK != null
                && VeilboundBlocks.AXIOM_CRUCIBLE_BLOCK != null
                && VeilboundBlocks.HORIZON_STABILIZER_BLOCK != null;
    }

'''
if 'private static boolean legacyRegistrationsAvailable()' not in text:
    if helper_marker not in text:
        raise SystemExit('could not locate EngineeringMonumentBlock hotfix insertion point')
    text = text.replace(helper_marker, helper + helper_marker, 1)
for signature, guard in [
    ('    public static List<AABB> collisionBoxes(BlockState state) {\n', '        if (!legacyRegistrationsAvailable()) return List.of();\n'),
    ('    public static boolean isMonument(BlockState state) {\n', '        if (!legacyRegistrationsAvailable()) return false;\n'),
    ('    private static VoxelShape shapeFor(BlockState state) {\n', '        if (!legacyRegistrationsAvailable()) return Shapes.block();\n'),
]:
    guarded = signature + guard
    if guarded not in text:
        if signature not in text:
            raise SystemExit(f'could not locate EngineeringMonumentBlock method: {signature.strip()}')
        text = text.replace(signature, guarded, 1)
monument.write_text(text, encoding='utf-8')

controller = root / 'src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeEngineeringStationController.java'
text = controller.read_text(encoding='utf-8')
old = '''        if (block==VeilboundBlocks.CHRONAL_ENGINE_BLOCK.get()
                || block==VeilboundBlocks.MNEMONIC_NEXUS_BLOCK.get()
                || block==VeilboundBlocks.AXIOM_CRUCIBLE_BLOCK.get()
                || block==VeilboundBlocks.HORIZON_STABILIZER_BLOCK.get()) {
'''
new = '''        if (VeilboundBlocks.CHRONAL_ENGINE_BLOCK != null
                && VeilboundBlocks.MNEMONIC_NEXUS_BLOCK != null
                && VeilboundBlocks.AXIOM_CRUCIBLE_BLOCK != null
                && VeilboundBlocks.HORIZON_STABILIZER_BLOCK != null
                && (block==VeilboundBlocks.CHRONAL_ENGINE_BLOCK.get()
                || block==VeilboundBlocks.MNEMONIC_NEXUS_BLOCK.get()
                || block==VeilboundBlocks.AXIOM_CRUCIBLE_BLOCK.get()
                || block==VeilboundBlocks.HORIZON_STABILIZER_BLOCK.get())) {
'''
if new not in text:
    if old not in text:
        raise SystemExit('could not locate engineering monument right-click branch')
    text = text.replace(old, new, 1)
controller.write_text(text, encoding='utf-8')

entity = root / 'src/main/java/dev/futurae/veilbound/block/entity/EngineeringMonumentBlockEntity.java'
text = entity.read_text(encoding='utf-8')
signature = '    public static @Nullable EngineeringMonumentKind kind(BlockState state) {\n'
guard = '''        if (VeilboundBlocks.CHRONAL_ENGINE_BLOCK == null
                || VeilboundBlocks.MNEMONIC_NEXUS_BLOCK == null
                || VeilboundBlocks.AXIOM_CRUCIBLE_BLOCK == null
                || VeilboundBlocks.HORIZON_STABILIZER_BLOCK == null) return null;
'''
if signature + guard not in text:
    if signature not in text:
        raise SystemExit('could not locate EngineeringMonumentBlockEntity.kind')
    text = text.replace(signature, signature + guard, 1)
entity.write_text(text, encoding='utf-8')

# Terminal/Core GUI polish is intentionally kept as reviewable patches against the exact 0.1.66
# source baseline. The first patch also carries the verifier-safe VEIL_LANCE null guard used by the tested hotfix.
patch_file = ci / 'gui-polish.patch'
if not patch_file.is_file():
    raise SystemExit('missing 0.1.67 GUI polish patch')
subprocess.run(['patch', '-p1', '--batch', '-i', str(patch_file)], cwd=root, check=True)

# Match the current ME-terminal interaction model more closely: left click withdraws a full stack,
# right click withdraws half a stack, while the server remains authoritative over the requested amount.
ae2_patch = ci / 'ae2-withdrawal-polish.patch'
if not ae2_patch.is_file():
    raise SystemExit('missing 0.1.67 AE-style withdrawal patch')
subprocess.run(['patch', '-p1', '--batch', '-i', str(ae2_patch)], cwd=root, check=True)

# Apply the broader post-test polish pass: complete vanilla Matter coverage, persistent terminal mode,
# shared vanilla GUI styling, distinct ore animations/drops, adjacent Void Anchor placement, and
# the wispy Genesis Seed asset with color isolated to its center.
feature_pass = ci / 'apply-feature-pass.py'
if not feature_pass.is_file():
    raise SystemExit('missing 0.1.67 feature-pass applicator')
subprocess.run([sys.executable, str(feature_pass), str(root)], check=True)

terminal = root / 'src/main/java/dev/futurae/veilbound/client/screen/VeilInventoryScreen.java'
terminal_text = terminal.read_text(encoding='utf-8')
if 'ContainerInput.PICKUP' not in terminal_text or 'setTooltipForNextFrame(font, stack' not in terminal_text:
    raise SystemExit('Veil Inventory GUI polish did not apply')
if '(maxStack + 1) / 2' not in terminal_text:
    raise SystemExit('ME-style half-stack withdrawal polish did not apply')
if 'VeilInventoryPreferences.craftingMode()' not in terminal_text:
    raise SystemExit('persistent Veil Inventory mode did not apply')
server_terminal = root / 'src/main/java/dev/futurae/veilbound/platform/neoforge/inventory/NeoForgeVeilInventoryController.java'
server_terminal_text = server_terminal.read_text(encoding='utf-8')
if 'Math.min(payload.resource().getMaxStackSize(), Math.max(1, payload.quantity()))' not in server_terminal_text:
    raise SystemExit('server withdrawal quantity guard did not apply')
core_screen = root / 'src/main/java/dev/futurae/veilbound/client/screen/DomainControlsScreen.java'
core_text = core_screen.read_text(encoding='utf-8')
if 'completely covered the tabs, expansion toggle, and six direction buttons' not in core_text:
    raise SystemExit('Core control widget-layer fix did not apply')
collision = root / 'src/main/java/dev/futurae/veilbound/block/EngineeringMonumentCollisionState.java'
if 'VeilboundBlocks.VEIL_LANCE != null' not in collision.read_text(encoding='utf-8'):
    raise SystemExit('VEIL_LANCE collision null guard did not apply')

print('VEILBOUND_0167_APPLY=PASS floating_crystal_core=staged material=physical_prismatic fragments=same_material levels=5 monument_null_safety=PASS gui_polish=PASS core_buttons=PASS ae_withdrawal=PASS feature_polish=PASS')
