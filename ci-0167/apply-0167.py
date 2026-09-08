from pathlib import Path
import shutil, sys

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

print('VEILBOUND_0167_APPLY=PASS floating_crystal_core=staged material=physical_prismatic fragments=same_material levels=5')
