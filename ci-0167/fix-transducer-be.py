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

# Domain lifecycle visual pass. Travel uses a brief black/purple full-screen vortex with opposite
# enter/exit spin. First Genesis Seed binding uses a longer singularity-style collapse/release and
# replaces the old success chat line entirely.
domain_transition_pass = ci / 'domain-transition-pass.py'
if not domain_transition_pass.is_file():
    raise SystemExit('missing Domain transition visual pass')
subprocess.run([sys.executable, str(domain_transition_pass), str(root)], check=True)

# The binding animation is now the only success feedback; remove the historical success translation
# too rather than leaving a dead message key in the cleaned first-release resources.
lang = root / 'src/main/resources/assets/veilbound/lang/en_us.json'
translations = json.loads(lang.read_text(encoding='utf-8'))
translations.pop('message.veilbound.genesis_seed.bound', None)
lang.write_text(json.dumps(translations, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

print(
    f'VEILBOUND_0167_TRANSDUCER_BE_FIX=PASS sha256={sha} bytes={len(raw)} '
    'models=raised_core textures=casing_panel_animated_core legacy_flat=absent')
print('VEILBOUND_0167_TERMINAL_REFERENCE_UI=PASS slots=beveled grid=recessed scrollbar=integrated track_click=page_jump header=compact')
print('VEILBOUND_0167_DOMAIN_TRANSITIONS=PASS enter_exit=black_purple_vortex binding=singularity binding_text=none')
