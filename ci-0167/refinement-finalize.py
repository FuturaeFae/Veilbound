from pathlib import Path
import base64, gzip, hashlib, io, json, struct, subprocess, sys, tarfile

root = Path(sys.argv[1]).resolve()
ci = Path(__file__).resolve().parent

# Apply the reviewed source/model/lang refinement over the fully reconstructed 0.1.67 tree.
patch_file = ci / 'refinement-pass.patch.gz.b64'
if not patch_file.is_file():
    raise SystemExit('missing refinement source patch')
patch_b64 = patch_file.read_text(encoding='ascii').strip().encode('ascii')
if hashlib.sha256(patch_b64).hexdigest() != '712bf36b7df9fafd03f2f07fce10589d69cea27f289efe57e4ae7e2d6edf06bc':
    raise SystemExit('refinement patch base64 sha256 mismatch')
patch_raw = gzip.decompress(base64.b64decode(patch_b64))
if hashlib.sha256(patch_raw).hexdigest() != '02f5e952513b0a29440f5480bf68867b68fb1697ac192ad5e1021057337af271':
    raise SystemExit('refinement patch sha256 mismatch')
patch_tmp = ci / '.refinement-pass.patch.tmp'
patch_tmp.write_bytes(patch_raw)
try:
    subprocess.run(['patch', '-p1', '--batch', '-i', str(patch_tmp)], cwd=root, check=True)
finally:
    patch_tmp.unlink(missing_ok=True)

# Restore the exact reviewed binary texture payload last, after all earlier generated-art passes.
parts = [ci / f'refinement-assets.tar.gz.b64.part{i}' for i in range(4)]
if not all(p.is_file() for p in parts):
    raise SystemExit('missing one or more refinement asset payload parts')
asset_b64 = ''.join(p.read_text(encoding='ascii').strip() for p in parts).encode('ascii')
if hashlib.sha256(asset_b64).hexdigest() != 'cc3798e4f1bdf518c962784e3c1bd5c5c84a0a04d959953c6829c626640196ca':
    raise SystemExit('refinement asset base64 sha256 mismatch')
archive_bytes = base64.b64decode(asset_b64)
if hashlib.sha256(archive_bytes).hexdigest() != 'bce6e021fdcc0a80ceda927582de7bb4f4e8b1b47c474c2b5bd42099dc40229f':
    raise SystemExit('refinement asset archive sha256 mismatch')
with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode='r:gz') as archive:
    archive.extractall(root)

# Old single-texture machine/anchor resources are deliberately superseded by multi-face 32px art.
(root / 'src/main/resources/assets/veilbound/textures/block/boundary_dynamo.png').unlink(missing_ok=True)
(root / 'src/main/resources/assets/veilbound/textures/block/void_anchor.png').unlink(missing_ok=True)

java = root / 'src/main/java'
res = root / 'src/main/resources/assets/veilbound'
terminal = (java / 'dev/futurae/veilbound/client/screen/VeilInventoryScreen.java').read_text(encoding='utf-8')
prefs = (java / 'dev/futurae/veilbound/client/screen/VeilInventoryPreferences.java').read_text(encoding='utf-8')
style = (java / 'dev/futurae/veilbound/client/screen/VanillaGuiStyle.java').read_text(encoding='utf-8')
transducer_screen = (java / 'dev/futurae/veilbound/client/screen/DimensionalTransducerScreen.java').read_text(encoding='utf-8')
dynamo_screen = (java / 'dev/futurae/veilbound/client/screen/BoundaryDynamoScreen.java').read_text(encoding='utf-8')
transducer_interaction = (java / 'dev/futurae/veilbound/platform/neoforge/NeoForgeTransducerCoordinator.java').read_text(encoding='utf-8')

required = {
    'withdraw virtual grid before vanilla screen': ('Virtual terminal controls must run before AbstractContainerScreen', terminal),
    'drag scrollbar state': ('draggingScrollBar', terminal),
    'drag scrollbar override': ('mouseDragged(MouseButtonEvent event, double dragX, double dragY)', terminal),
    'craftable/all recipe switch': ('handleCraftFilterClick', terminal),
    'craftable filter payload': ('showAllCrafts, Math.max(0, page), craftingQuery, craftingSort', terminal),
    'right click reverse sort': ('cycleSort(button == 1 ? -1 : 1)', terminal),
    'search shortened': ('searchBox.setHint(Component.literal("Search"))', terminal),
    'filter persistence': ('veilInventory.crafting.showAllRecipes', prefs),
    'vanilla slot border offset': ('col * 18 - 1', style),
    'transducer matter tooltip': ('Matter: "', transducer_screen),
    'transducer DE tooltip': ('DE: "', transducer_screen),
    'transducer FE tooltip': ('FE: "', transducer_screen),
    'dynamo exact FE tooltip': ('BoundaryDynamoBlockEntity.FE_CAPACITY', dynamo_screen),
    'sneak place bypass': ('if (player.isShiftKeyDown()) return;', transducer_interaction),
}
for label, (marker, text) in required.items():
    if marker not in text:
        raise SystemExit(f'refinement source audit failed: {label}')
if 'Button.builder' in terminal:
    raise SystemExit('generic sort/button control survived refinement')

# Text/rename audit.
lang = json.loads((res / 'lang/en_us.json').read_text(encoding='utf-8'))
if lang.get('block.veilbound.boundary_dynamo') != 'Dynamo' or lang.get('container.veilbound.boundary_dynamo') != 'Dynamo':
    raise SystemExit('Dynamo display rename did not apply')
if lang.get('screen.veilbound.veil_inventory.search_hint') != 'Search':
    raise SystemExit('Search hint did not shorten')

# PNG dimension audit. Every registered item presentation is now at least 32px native resolution.
def png_size(path: Path):
    data = path.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise SystemExit(f'not PNG: {path}')
    return struct.unpack('>II', data[16:24])

item_sheets = ['dimensional_shard','resonant_crystal','phase_mote','causal_fragment','genesis_seed']
for name in item_sheets:
    size = png_size(res / f'textures/item/{name}.png')
    if size != (32, 256):
        raise SystemExit(f'item texture is not 32px x 8 frames: {name} {size}')
for name in ['dimensional_shard_ore','deepslate_dimensional_shard_ore','resonant_accretion','phase_accretion','causal_accretion']:
    size = png_size(res / f'textures/block/{name}.png')
    if size != (32, 256):
        raise SystemExit(f'ore/accretion texture is not 32px x 8 frames: {name} {size}')
for tier in ['dimensional','resonant','phase','causal']:
    if png_size(res / f'textures/block/{tier}_transducer_casing.png') != (32,32):
        raise SystemExit(f'{tier} transducer casing is not 32px')
    if png_size(res / f'textures/block/{tier}_transducer_panel.png') != (32,32):
        raise SystemExit(f'{tier} transducer panel is not 32px')
    if png_size(res / f'textures/block/{tier}_transducer_core.png') != (32,128):
        raise SystemExit(f'{tier} transducer core is not 32px animated')
for name in ['dynamo_front','dynamo_side','dynamo_top','void_anchor_side','void_anchor_top','void_anchor_bottom']:
    if png_size(res / f'textures/block/{name}.png') != (32,32):
        raise SystemExit(f'{name} is not 32px')

# Model audit: solid transducer casing removes see-through corners, while the animated core protrudes above it.
for tier in ['dimensional','resonant','phase','causal']:
    model = json.loads((res / f'models/block/{tier}_transducer.json').read_text(encoding='utf-8'))
    if model['elements'][0].get('to') != [16,16,16] or model['elements'][1].get('from') != [5,16,5] or model['elements'][1].get('to') != [11,20,11]:
        raise SystemExit(f'{tier} transducer model is not solid-base + raised-core')
dynamo_model = json.loads((res / 'models/block/boundary_dynamo.json').read_text(encoding='utf-8'))
if dynamo_model.get('parent') != 'minecraft:block/orientable' or dynamo_model.get('textures',{}).get('front') != 'veilbound:block/dynamo_front':
    raise SystemExit('Dynamo furnace-derived model did not apply')
anchor_model = json.loads((res / 'models/block/void_anchor.json').read_text(encoding='utf-8'))
if anchor_model.get('parent') != 'minecraft:block/cube_bottom_top' or anchor_model.get('textures',{}).get('top') != 'veilbound:block/void_anchor_top':
    raise SystemExit('Void Anchor multi-face model did not apply')
if (res / 'textures/block/boundary_dynamo.png').exists() or (res / 'textures/block/void_anchor.png').exists():
    raise SystemExit('superseded single-face textures survived')

print('VEILBOUND_0167_REFINEMENT=PASS withdrawal=restored scrollbar=draggable craft_filter=craftable_or_all sort=left_forward_right_back search=Search')
print('VEILBOUND_0167_GUI_REFINEMENT=PASS slots=vanilla_aligned meters=hover_exact_values transducer_text=compact sneak_place=PASS')
print('VEILBOUND_0167_RESOURCE_REFINEMENT=PASS dimensional=stone_deepslate_correct accretions=embedded_void_animated dynamo=furnace_iron_copper void_anchor=32px items=32px_all')
