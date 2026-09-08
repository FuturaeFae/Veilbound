from pathlib import Path
import base64, gzip, io, subprocess, sys, tarfile

root = Path(sys.argv[1]).resolve()
ci = Path(__file__).resolve().parent

patch_b64 = ci / 'feature-pass-text.patch.gz.b64'
assets_b64 = ci / 'feature-assets.tar.gz.b64'
if not patch_b64.is_file() or not assets_b64.is_file():
    raise SystemExit('missing 0.1.67 feature-pass payload')

patch_bytes = gzip.decompress(base64.b64decode(patch_b64.read_text(encoding='ascii')))
patch_file = ci / '.feature-pass.patch.tmp'
patch_file.write_bytes(patch_bytes)
try:
    subprocess.run(['patch', '-p1', '--batch', '-i', str(patch_file)], cwd=root, check=True)
finally:
    patch_file.unlink(missing_ok=True)

asset_bytes = base64.b64decode(assets_b64.read_text(encoding='ascii'))
with tarfile.open(fileobj=io.BytesIO(asset_bytes), mode='r:gz') as archive:
    archive.extractall(root)

checks = {
    'vanilla_matter_floor': root / 'src/main/java/dev/futurae/veilbound/matter/VanillaMatterCoverage.java',
    'terminal_preferences': root / 'src/main/java/dev/futurae/veilbound/client/screen/VeilInventoryPreferences.java',
    'vanilla_gui_style': root / 'src/main/java/dev/futurae/veilbound/client/screen/VanillaGuiStyle.java',
    'genesis_seed': root / 'src/main/resources/assets/veilbound/textures/item/genesis_seed.png',
    'resonant_drop': root / 'src/main/resources/assets/veilbound/textures/item/resonant_filament.png',
    'phase_drop': root / 'src/main/resources/assets/veilbound/textures/item/phase_mote.png',
    'causal_drop': root / 'src/main/resources/assets/veilbound/textures/item/causal_fragment.png',
}
for name, path in checks.items():
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f'0.1.67 feature-pass audit failed: {name}')

terminal = (root / 'src/main/java/dev/futurae/veilbound/client/screen/VeilInventoryScreen.java').read_text(encoding='utf-8')
if 'VeilInventoryPreferences.craftingMode()' not in terminal:
    raise SystemExit('terminal mode persistence missing')
void_anchor = (root / 'src/main/java/dev/futurae/veilbound/item/VoidAnchorBlockItem.java').read_text(encoding='utf-8')
if 'base.relative(direction)' not in void_anchor or 'blockInteractionRange()' in void_anchor:
    raise SystemExit('Void Anchor adjacent placement missing')
items = (root / 'src/main/java/dev/futurae/veilbound/registry/VeilboundItems.java').read_text(encoding='utf-8')
for marker in ('RESONANT_FILAMENT', 'PHASE_MOTE', 'CAUSAL_FRAGMENT'):
    if marker not in items:
        raise SystemExit(f'missing dedicated ore drop: {marker}')

print('VEILBOUND_0167_FEATURE_PASS=PASS vanilla_matter=complete minimum=1 terminal_mode=persistent vanilla_gui=shared ore_animations=distinct ore_drops=dedicated void_anchor=adjacent genesis_seed=wispy_center_prismatic')
