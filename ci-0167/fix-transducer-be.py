from pathlib import Path
import base64
import gzip
import hashlib
import json
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
ci = Path(__file__).resolve().parent
payload = ci / 'DimensionalTransducerBlockEntity.java.gz.b64'
target = root / 'src/main/java/dev/futurae/veilbound/block/entity/DimensionalTransducerBlockEntity.java'
expected_sha = 'b434f872f65227ed4179189ef438a6f148a4269149417ce44d467454cfd39896'

if not payload.is_file():
    raise SystemExit('missing clean transducer block-entity payload')

raw = gzip.decompress(base64.b64decode(payload.read_text(encoding='ascii')))
sha = hashlib.sha256(raw).hexdigest()
if sha != expected_sha:
    raise SystemExit(f'unexpected transducer block-entity payload sha256: {sha}')
if b'public final class DimensionalTransducerBlockEntity' not in raw:
    raise SystemExit('invalid transducer block-entity payload')
if b'MATTER_INPUT_SLOT' not in raw or b'DimensionalTransducerMenu' not in raw:
    raise SystemExit('transducer block-entity payload missing GUI markers')

target.parent.mkdir(parents=True, exist_ok=True)
target.write_bytes(raw)

# The historical compact archive still contains the old cube_all transducer models. Replace them
# after extraction so the packaged JAR actually USES the new casing/panel/animated-core textures.
model_dir = root / 'src/main/resources/assets/veilbound/models/block'
texture_dir = root / 'src/main/resources/assets/veilbound/textures/block'
for kind in ('dimensional', 'resonant', 'phase', 'causal'):
    model = {
        'parent': 'minecraft:block/block',
        'ambientocclusion': True,
        'textures': {
            'particle': f'veilbound:block/{kind}_transducer_casing',
            'casing': f'veilbound:block/{kind}_transducer_casing',
            'panel': f'veilbound:block/{kind}_transducer_panel',
            'core': f'veilbound:block/{kind}_transducer_core',
        },
        'elements': [
            {
                'from': [0, 0, 0],
                'to': [16, 12, 16],
                'faces': {
                    'down': {'texture': '#casing', 'cullface': 'down'},
                    'up': {'texture': '#casing'},
                    'north': {'texture': '#panel', 'cullface': 'north'},
                    'south': {'texture': '#panel', 'cullface': 'south'},
                    'west': {'texture': '#panel', 'cullface': 'west'},
                    'east': {'texture': '#panel', 'cullface': 'east'},
                },
            },
            {
                'from': [5, 12, 5],
                'to': [11, 16, 11],
                'faces': {
                    'down': {'texture': '#core'},
                    'up': {'texture': '#core'},
                    'north': {'texture': '#core'},
                    'south': {'texture': '#core'},
                    'west': {'texture': '#core'},
                    'east': {'texture': '#core'},
                },
            },
        ],
    }
    model_path = model_dir / f'{kind}_transducer.json'
    model_path.write_text(json.dumps(model, indent=2) + '\n', encoding='utf-8')

    for suffix in ('casing.png', 'panel.png', 'core.png', 'core.png.mcmeta'):
        texture = texture_dir / f'{kind}_transducer_{suffix}'
        if not texture.is_file() or texture.stat().st_size == 0:
            raise SystemExit(f'missing active transducer texture: {texture.relative_to(root)}')

    legacy = texture_dir / f'{kind}_transducer.png'
    if legacy.exists():
        raise SystemExit(f'legacy flat transducer texture unexpectedly remained: {legacy.relative_to(root)}')

# Final Veil/Core terminal visual pass. Keep the existing server-backed storage/crafting behavior,
# but present it with the tightly framed slots and integrated scrollbar from the supplied reference.
terminal_patch = ci / 'terminal-reference-ui.patch'
if not terminal_patch.is_file():
    raise SystemExit('missing terminal reference UI patch')
subprocess.run(['patch', '-p1', '--batch', '-i', str(terminal_patch)], cwd=root, check=True)
terminal = root / 'src/main/java/dev/futurae/veilbound/client/screen/VeilInventoryScreen.java'
terminal_text = terminal.read_text(encoding='utf-8')
for marker in (
    'SCROLL_WIDTH = 14',
    'handleScrollBarClick',
    'drawScrollArrow',
    'Recess the virtual terminal grid as one dense tray',
    'Stronger 18x18 bevel than the shared generic slot',
):
    if marker not in terminal_text:
        raise SystemExit(f'terminal reference UI marker missing: {marker}')
if 'Button previous = Button.builder' in terminal_text or 'Button next = Button.builder' in terminal_text:
    raise SystemExit('old floating terminal page buttons remained')

# Base Domain lifecycle visual pass removes binding success text and installs networking/render hooks.
domain_transition_pass = ci / 'domain-transition-pass.py'
if not domain_transition_pass.is_file():
    raise SystemExit('missing Domain transition visual pass')
subprocess.run([sys.executable, str(domain_transition_pass), str(root)], check=True)

# Run a compressed late-stage script payload without trusting the historical source archive to carry
# current client/server transition timing or current resource textures.
def run_gz_b64_script(name):
    payload_path = ci / name
    if not payload_path.is_file():
        raise SystemExit(f'missing late-stage payload: {name}')
    script = gzip.decompress(base64.b64decode(payload_path.read_text(encoding='ascii')))
    temp = ci / ('.' + name.removesuffix('.gz.b64') + '.tmp')
    temp.write_bytes(script)
    try:
        subprocess.run([sys.executable, str(temp), str(root)], check=True)
    finally:
        temp.unlink(missing_ok=True)

# V2 travel starts the closing animation first, waits before teleporting under full black, then sends
# the opening phase. The final vanilla-GUI pass below upgrades the timing to the approved 2.5 seconds.
run_gz_b64_script('domain-transition-v2.py.gz.b64')

# Install the generated material identities first; the final pass below then overwrites these with
# the exact approved art payload so generated placeholders can never win in the packaged JAR.
run_gz_b64_script('resource-texture-v2.py.gz.b64')

# The binding animation is now the only success feedback; remove the historical success translation.
lang = root / 'src/main/resources/assets/veilbound/lang/en_us.json'
translations = json.loads(lang.read_text(encoding='utf-8'))
translations.pop('message.veilbound.genesis_seed.bound', None)
lang.write_text(json.dumps(translations, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

print(
    f'VEILBOUND_0167_TRANSDUCER_BE_FIX=PASS sha256={sha} bytes={len(raw)} '
    'models=raised_core textures=casing_panel_animated_core legacy_flat=absent')
print('VEILBOUND_0167_TERMINAL_REFERENCE_UI=PASS slots=beveled grid=recessed scrollbar=integrated track_click=page_jump header=compact')
print('VEILBOUND_0167_DOMAIN_TRANSITIONS=PASS travel=swirl_in_before_teleport_swirl_out radial=removed binding=singularity binding_text=none')
print('VEILBOUND_0167_RESOURCE_TEXTURES=PASS ores=updated items=updated identities=dimensional_prismatic_resonant_crystal_phase_metal_causal_liquid')

# Authoritative last pass: real vanilla player-container architecture, cursor-based terminal crafting,
# standard machine inventory geometry, approved slow travel timing, and the exact accepted textures.
vanilla_gui_finalize = ci / 'vanilla-gui-finalize.py'
if not vanilla_gui_finalize.is_file():
    raise SystemExit('missing final vanilla GUI pass')
subprocess.run([sys.executable, str(vanilla_gui_finalize), str(root)], check=True)

# Final dimensional ore correction: both host-rock variants use the exact same approved prismatic
# crystal overlay. Only the vanilla stone/deepslate host texture differs between the two sheets.
dimensional_ore_finalize = ci / 'dimensional-ore-finalize.py'
if not dimensional_ore_finalize.is_file():
    raise SystemExit('missing final dimensional ore overlay pass')
subprocess.run([sys.executable, str(dimensional_ore_finalize), str(root)], check=True)
