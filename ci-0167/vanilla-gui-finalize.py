from pathlib import Path
import base64
import gzip
import hashlib
import io
import struct
import subprocess
import sys
import tarfile

root = Path(sys.argv[1]).resolve()
ci = Path(__file__).resolve().parent

# Apply the architectural GUI pass after all historical source reconstruction. This converts the
# Veil terminal to a real AbstractContainerScreen/Menu for the player's 36 vanilla slots, places
# synthesis/crafting results on Minecraft's carried cursor stack, and normalizes machine screens.
patch_payload = ci / 'vanilla-gui-pass.patch.gz.b64'
if not patch_payload.is_file():
    raise SystemExit('missing vanilla GUI patch payload')
patch_b64 = patch_payload.read_text(encoding='ascii').strip().encode('ascii')
# Base64 transport can differ harmlessly in wrapping/terminal newline. Validate the decoded patch
# itself, which is the authoritative byte stream applied to the reconstructed source.
patch_raw = gzip.decompress(base64.b64decode(patch_b64))
if hashlib.sha256(patch_raw).hexdigest() != '5eddbaf90da165f4eb235c4eea0b4102a3571b309fbd62d85e4117f763edcb29':
    raise SystemExit('decoded vanilla GUI patch sha256 mismatch')
patch_tmp = ci / '.vanilla-gui-pass.patch.tmp'
patch_tmp.write_bytes(patch_raw)
try:
    subprocess.run(['patch', '-p1', '--batch', '-i', str(patch_tmp)], cwd=root, check=True)
finally:
    patch_tmp.unlink(missing_ok=True)

# Restore the exact approved resource sprites after every generated/legacy texture pass. The payload
# is split only to keep repository text blobs manageable; concatenation is byte-exact base64.
parts = [ci / f'agreed-resource-textures.tar.gz.b64.part{i}' for i in range(4)]
if not all(part.is_file() for part in parts):
    raise SystemExit('missing one or more approved texture payload parts')
texture_b64 = ''.join(part.read_text(encoding='ascii').strip() for part in parts).encode('ascii')
if hashlib.sha256(texture_b64).hexdigest() != '4e1927f917fbbf21e46c8ab84595c4418345d53ce6f044a5c39b27aac258bf8b':
    raise SystemExit('approved texture payload base64 sha256 mismatch')
texture_archive = base64.b64decode(texture_b64)
if hashlib.sha256(texture_archive).hexdigest() != '49245587c6f78e962f5548c995119e33ef657fd856ab7c957791edfbf6c644ed':
    raise SystemExit('approved texture archive sha256 mismatch')
with tarfile.open(fileobj=io.BytesIO(texture_archive), mode='r:gz') as archive:
    archive.extractall(root)

# Source-level architecture audit. A future reconstruction must fail instead of silently returning
# to hand-painted fake player inventory slots or item-to-inventory crafting behavior.
java = root / 'src/main/java'
terminal = (java / 'dev/futurae/veilbound/client/screen/VeilInventoryScreen.java').read_text(encoding='utf-8')
menu = (java / 'dev/futurae/veilbound/menu/VeilInventoryMenu.java').read_text(encoding='utf-8')
menus = (java / 'dev/futurae/veilbound/registry/VeilboundMenus.java').read_text(encoding='utf-8')
inv_controller = (java / 'dev/futurae/veilbound/platform/neoforge/inventory/NeoForgeVeilInventoryController.java').read_text(encoding='utf-8')
crafting = (java / 'dev/futurae/veilbound/platform/neoforge/inventory/NeoForgeVeilCraftingController.java').read_text(encoding='utf-8')
transducer = (java / 'dev/futurae/veilbound/client/screen/DimensionalTransducerScreen.java').read_text(encoding='utf-8')
transducer_menu = (java / 'dev/futurae/veilbound/menu/DimensionalTransducerMenu.java').read_text(encoding='utf-8')
dynamo = (java / 'dev/futurae/veilbound/client/screen/BoundaryDynamoScreen.java').read_text(encoding='utf-8')
transition = (java / 'dev/futurae/veilbound/client/render/DomainTransitionOverlay.java').read_text(encoding='utf-8')
travel = (java / 'dev/futurae/veilbound/platform/neoforge/travel/NeoForgeDomainTravelExecutor.java').read_text(encoding='utf-8')

required = {
    'terminal real container screen': ('extends AbstractContainerScreen<VeilInventoryMenu>', terminal),
    'terminal real menu registry': ('VeilboundMenus.VEIL_INVENTORY', menu + menus),
    'server opens terminal menu': ('player.openMenu(new SimpleMenuProvider', inv_controller),
    'craft result placed on cursor': ('placeOnCursor(player, resultStack)', crafting),
    'transducer vanilla dimensions': ('super(menu, inventory, title, 176, 166)', transducer),
    'dynamo vanilla dimensions': ('super(menu, inventory, title, 176, 166)', dynamo),
    'transducer vanilla slot x': ('8 + column * 18', transducer_menu),
    'transducer vanilla slot y': ('84 + row * 18', transducer_menu),
    'slow swirl in': ('SWIRL_IN_NANOS = 1_250_000_000L', transition),
    'slow swirl out': ('SWIRL_OUT_NANOS = 1_250_000_000L', transition),
    'slow pre-teleport cover': ('SWIRL_IN_DELAY_TICKS = 25L', travel),
}
for label, (marker, text) in required.items():
    if marker not in text:
        raise SystemExit(f'vanilla GUI final audit failed: {label}')
if 'renderPlayerInventory(' in terminal or 'handleContainerInput(' in terminal:
    raise SystemExit('manual/fake player inventory path survived terminal conversion')

# Exact approved resource audit: all nine animated sheets are 16x128 and have animation metadata.
assets = root / 'src/main/resources/assets/veilbound/textures'
resource_paths = [
    assets / 'item/dimensional_shard.png',
    assets / 'item/resonant_crystal.png',
    assets / 'item/phase_mote.png',
    assets / 'item/causal_fragment.png',
    assets / 'block/dimensional_shard_ore.png',
    assets / 'block/deepslate_dimensional_shard_ore.png',
    assets / 'block/resonant_accretion.png',
    assets / 'block/phase_accretion.png',
    assets / 'block/causal_accretion.png',
]
for path in resource_paths:
    data = path.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise SystemExit(f'approved resource is not PNG: {path.name}')
    width, height = struct.unpack('>II', data[16:24])
    if (width, height) != (16, 128):
        raise SystemExit(f'approved resource wrong dimensions: {path.name} {width}x{height}')
    if not Path(str(path) + '.mcmeta').is_file():
        raise SystemExit(f'approved resource missing animation metadata: {path.name}')

print('VEILBOUND_0167_VANILLA_GUI_FINAL=PASS terminal=real_container player_slots=vanilla cursor=vanilla crafting_result=carried_stack transducer=dynamo_layout machines=176x166')
print('VEILBOUND_0167_AGREED_TEXTURES=PASS exact_payload=locked resources=9 frames=8 dimensions=16x128')
print('VEILBOUND_0167_SLOW_TELEPORT=PASS swirl_in=1.25s black_cover=1.25s_server_delay swirl_out=1.25s')
