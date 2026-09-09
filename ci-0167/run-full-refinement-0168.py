from pathlib import Path
import base64, gzip, hashlib, json, struct, subprocess, sys, traceback, zlib

RECOVERY_PATCH_B64_SHA = '712bf36b7df9fafd03f2f07fce10589d69cea27f289efe57e4ae7e2d6edf06bc'
RECOVERY_PATCH_RAW_SHA = '02f5e952513b0a29440f5480bf68867b68fb1697ac192ad5e1021057337af271'
FULL_PATCH_RAW_SHA = '80e5bf1a645bd3b55c7e665bbbb5dd2ed3d4edace29e239a7a70523e823dd66b'


def recover_gzip_deflate(data: bytes) -> bytes:
    if len(data) < 18 or data[:2] != b'\x1f\x8b' or data[2] != 8:
        raise ValueError('not a supported gzip member')
    flags = data[3]
    pos = 10
    if flags & 0x04:
        if pos + 2 > len(data):
            raise ValueError('truncated gzip FEXTRA')
        xlen = data[pos] | (data[pos + 1] << 8)
        pos += 2 + xlen
    if flags & 0x08:
        end = data.find(b'\x00', pos)
        if end < 0:
            raise ValueError('truncated gzip FNAME')
        pos = end + 1
    if flags & 0x10:
        end = data.find(b'\x00', pos)
        if end < 0:
            raise ValueError('truncated gzip FCOMMENT')
        pos = end + 1
    if flags & 0x02:
        pos += 2
    if pos >= len(data):
        raise ValueError('truncated gzip payload')

    # Decode only the raw DEFLATE member. This intentionally does not trust the broken gzip
    # CRC/ISIZE trailer; authenticity is established by the pre-existing decompressed SHA-256.
    decomp = zlib.decompressobj(-zlib.MAX_WBITS)
    raw = decomp.decompress(data[pos:]) + decomp.flush()
    if not decomp.eof:
        raise ValueError('gzip DEFLATE stream itself is truncated')
    return raw


def png_size(path: Path):
    data = path.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise SystemExit(f'not PNG: {path}')
    return struct.unpack('>II', data[16:24])


def decode_rgba(path: Path):
    data = path.read_bytes()
    pos = 8
    width = height = depth = ctype = None
    idat = []
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b'IHDR':
            width, height, depth, ctype, _, _, _ = struct.unpack('>IIBBBBB', body)
        elif typ == b'IDAT':
            idat.append(body)
        elif typ == b'IEND':
            break
    if depth != 8 or ctype != 6:
        raise SystemExit(f'expected RGBA8 PNG: {path}')
    raw = zlib.decompress(b''.join(idat))
    stride = width * 4
    rows, off, prev = [], 0, bytearray(stride)

    def paeth(a, b, c):
        p = a + b - c
        pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
        return a if pa <= pb and pa <= pc else (b if pb <= pc else c)

    for _ in range(height):
        filt = raw[off]
        off += 1
        scan = bytearray(raw[off:off + stride])
        off += stride
        out = bytearray(stride)
        for i, x in enumerate(scan):
            a = out[i - 4] if i >= 4 else 0
            b = prev[i]
            c = prev[i - 4] if i >= 4 else 0
            if filt == 0:
                v = x
            elif filt == 1:
                v = (x + a) & 255
            elif filt == 2:
                v = (x + b) & 255
            elif filt == 3:
                v = (x + ((a + b) // 2)) & 255
            elif filt == 4:
                v = (x + paeth(a, b, c)) & 255
            else:
                raise SystemExit(f'unsupported PNG filter {filt}: {path}')
            out[i] = v
        rows.append(bytes(out))
        prev = out
    return width, height, rows


def pixel(row, x):
    i = x * 4
    return tuple(row[i:i + 4])


def colorful(px):
    r, g, b, _ = px
    return max(r, g, b) > 60 and max(r, g, b) - min(r, g, b) >= 28


def audit(root: Path):
    java = root / 'src/main/java/dev/futurae/veilbound'
    res = root / 'src/main/resources/assets/veilbound'

    terminal = (java / 'client/screen/VeilInventoryScreen.java').read_text(encoding='utf-8')
    prefs = (java / 'client/screen/VeilInventoryPreferences.java').read_text(encoding='utf-8')
    style = (java / 'client/screen/VanillaGuiStyle.java').read_text(encoding='utf-8')
    menu = (java / 'menu/VeilInventoryMenu.java').read_text(encoding='utf-8')
    transducer_screen = (java / 'client/screen/DimensionalTransducerScreen.java').read_text(encoding='utf-8')
    dynamo_screen = (java / 'client/screen/BoundaryDynamoScreen.java').read_text(encoding='utf-8')
    transducer_interaction = (java / 'platform/neoforge/NeoForgeTransducerCoordinator.java').read_text(encoding='utf-8')
    anchor = (java / 'block/VoidAnchorBlock.java').read_text(encoding='utf-8')

    required = {
        'withdraw virtual grid before vanilla screen': ('Virtual terminal controls must run before AbstractContainerScreen', terminal),
        'drag scrollbar state': ('draggingScrollBar', terminal),
        'drag scrollbar override': ('mouseDragged(MouseButtonEvent event, double dragX, double dragY)', terminal),
        'craftable/all recipe switch': ('handleCraftFilterClick', terminal),
        'craftable filter payload': ('showAllCrafts, Math.max(0, page), craftingQuery, craftingSort', terminal + menu),
        'right click reverse sort': ('cycleSort(button == 1 ? -1 : 1)', terminal),
        'search shortened': ('searchBox.setHint(Component.literal("Search"))', terminal),
        'filter persistence': ('veilInventory.crafting.showAllRecipes', prefs),
        'vanilla slot border offset': ('col * 18 - 1', style),
        'transducer matter tooltip': ('Matter: "', transducer_screen),
        'transducer DE tooltip': ('DE: "', transducer_screen),
        'transducer FE tooltip': ('FE: "', transducer_screen),
        'dynamo exact FE tooltip': ('BoundaryDynamoBlockEntity.FE_CAPACITY', dynamo_screen),
        'sneak place bypass': ('if (player.isShiftKeyDown()) return;', transducer_interaction),
        'void anchor wisps': ('ParticleTypes.REVERSE_PORTAL', anchor),
        'void anchor animation tick': ('animateTick', anchor),
    }
    for label, (marker, text) in required.items():
        if marker not in text:
            raise SystemExit(f'0.1.68 source audit failed: {label}')
    if 'Button.builder' in terminal:
        raise SystemExit('generic sort/button control survived 0.1.68 refinement')

    lang = json.loads((res / 'lang/en_us.json').read_text(encoding='utf-8'))
    if lang.get('block.veilbound.boundary_dynamo') != 'Dynamo' or lang.get('container.veilbound.boundary_dynamo') != 'Dynamo':
        raise SystemExit('Dynamo display rename did not apply')

    item_sheets = ['dimensional_shard', 'resonant_crystal', 'phase_mote', 'causal_fragment', 'genesis_seed']
    for name in item_sheets:
        if png_size(res / f'textures/item/{name}.png') != (32, 256):
            raise SystemExit(f'item texture is not 32px x 8 frames: {name}')

    block_dir = res / 'textures/block'
    for p in block_dir.glob('*.png'):
        w, h, rows = decode_rgba(p)
        if w != 32:
            raise SystemExit(f'block texture is not 32px native width: {p.name} {w}x{h}')
        if any(row[i + 3] != 255 for row in rows for i in range(0, len(row), 4)):
            raise SystemExit(f'block texture has transparent pixels after refinement: {p.name}')

    for name in ['dimensional_shard_ore', 'deepslate_dimensional_shard_ore', 'resonant_accretion', 'phase_accretion', 'causal_accretion']:
        if png_size(block_dir / f'{name}.png') != (32, 256):
            raise SystemExit(f'ore/accretion texture is not 32px x 8 frames: {name}')
    for tier in ['dimensional', 'resonant', 'phase', 'causal']:
        if png_size(block_dir / f'{tier}_transducer_casing.png') != (32, 32):
            raise SystemExit(f'{tier} transducer casing is not 32px')
        if png_size(block_dir / f'{tier}_transducer_panel.png') != (32, 32):
            raise SystemExit(f'{tier} transducer panel is not 32px')
        if png_size(block_dir / f'{tier}_transducer_core.png') != (32, 128):
            raise SystemExit(f'{tier} transducer core is not 32px animated')
    if png_size(block_dir / 'dynamo_front.png') != (32, 128):
        raise SystemExit('Dynamo front is not 32px x 4 frames')
    for name in ['dynamo_side', 'dynamo_top']:
        if png_size(block_dir / f'{name}.png') != (32, 32):
            raise SystemExit(f'{name} is not 32px')
    for name in ['void_anchor_side', 'void_anchor_top', 'void_anchor_bottom']:
        if png_size(block_dir / f'{name}.png') != (32, 128):
            raise SystemExit(f'{name} is not 32px x 4 frames')
        if not (block_dir / f'{name}.png.mcmeta').is_file():
            raise SystemExit(f'{name} animation metadata missing')

    sw, sh, srows = decode_rgba(block_dir / 'dimensional_shard_ore.png')
    dw, dh, drows = decode_rgba(block_dir / 'deepslate_dimensional_shard_ore.png')
    if (sw, sh) != (dw, dh):
        raise SystemExit('dimensional ore host sheets differ in dimensions')
    smask = [[colorful(pixel(srows[y], x)) for x in range(sw)] for y in range(sh)]
    dmask = [[colorful(pixel(drows[y], x)) for x in range(dw)] for y in range(dh)]
    if smask != dmask:
        raise SystemExit('stone/deepslate dimensional ore resource masks differ')

    for tier in ['dimensional', 'resonant', 'phase', 'causal']:
        model = json.loads((res / f'models/block/{tier}_transducer.json').read_text(encoding='utf-8'))
        elems = model.get('elements', [])
        if not any(e.get('from') == [0, 0, 0] and e.get('to') == [16, 16, 16] for e in elems):
            raise SystemExit(f'{tier} transducer is not a solid full-block model')

    dynamo_model = json.loads((res / 'models/block/boundary_dynamo.json').read_text(encoding='utf-8'))
    if dynamo_model.get('parent') != 'minecraft:block/orientable' or dynamo_model.get('textures', {}).get('front') != 'veilbound:block/dynamo_front':
        raise SystemExit('Dynamo furnace-derived model did not apply')
    anchor_model = json.loads((res / 'models/block/void_anchor.json').read_text(encoding='utf-8'))
    if anchor_model.get('parent') != 'minecraft:block/cube_bottom_top' or anchor_model.get('textures', {}).get('top') != 'veilbound:block/void_anchor_top':
        raise SystemExit('Void Anchor multi-face model did not apply')
    if (block_dir / 'boundary_dynamo.png').exists() or (block_dir / 'void_anchor.png').exists():
        raise SystemExit('superseded single-face textures survived')

    print('VEILBOUND_0168_FULL_AUDIT=PASS terminal=interactive machines=precise sneak_place=PASS void_anchor=wisps')
    print('VEILBOUND_0168_RESOURCE_AUDIT=PASS native=32px ores=host_parity transducers=solid dynamo=animated anchor=animated')


def choose_patch(ci: Path) -> tuple[bytes, str]:
    full_payload = ci / 'full-refinement-pass.patch.gz.b64'
    if full_payload.is_file():
        try:
            encoded = full_payload.read_text(encoding='ascii').strip().encode('ascii')
            gzip_bytes = base64.b64decode(encoded, validate=True)
            patch = recover_gzip_deflate(gzip_bytes)
            recovered_sha = hashlib.sha256(patch).hexdigest()
            print(f'VEILBOUND_0168_FULL_PATCH_DEFLATE recovered_bytes={len(patch)} sha256={recovered_sha}')
            if recovered_sha == FULL_PATCH_RAW_SHA:
                return patch, 'full_deflate_sha_verified'
            print('VEILBOUND_0168_FULL_PATCH_DEFLATE=REJECT raw_sha_mismatch')
        except Exception as exc:
            print(f'VEILBOUND_0168_FULL_PATCH_DEFLATE=REJECT {type(exc).__name__}: {exc}')

    recovery = ci / 'refinement-pass.patch.gz.b64'
    if not recovery.is_file():
        raise SystemExit('no usable refinement source patch payload')
    pb64 = recovery.read_text(encoding='ascii').strip().encode('ascii')
    if hashlib.sha256(pb64).hexdigest() != RECOVERY_PATCH_B64_SHA:
        raise SystemExit('recovery refinement patch base64 sha mismatch')
    patch = gzip.decompress(base64.b64decode(pb64, validate=True))
    if hashlib.sha256(patch).hexdigest() != RECOVERY_PATCH_RAW_SHA:
        raise SystemExit('recovery refinement patch raw sha mismatch')
    return patch, 'earlier_sha_verified'


def main():
    root = Path(sys.argv[1]).resolve()
    ci = Path(__file__).resolve().parent
    generator = ci / 'generate-full-refinement-assets.py'
    if not generator.is_file():
        raise SystemExit('missing 0.1.68 deterministic asset generator')

    patch, patch_source = choose_patch(ci)
    print(f'VEILBOUND_0168_RECOVERY_PATCH=PASS source={patch_source} bytes={len(patch)} sha256={hashlib.sha256(patch).hexdigest()}')

    patch_tmp = ci / '.refinement-0168-recovery.patch.tmp'
    patch_tmp.write_bytes(patch)
    try:
        subprocess.run(['patch', '-p1', '--batch', '-i', str(patch_tmp)], cwd=root, check=True)
    finally:
        patch_tmp.unlink(missing_ok=True)

    subprocess.run([sys.executable, str(generator), str(root)], check=True)
    (root / 'src/main/resources/assets/veilbound/textures/block/boundary_dynamo.png').unlink(missing_ok=True)
    (root / 'src/main/resources/assets/veilbound/textures/block/void_anchor.png').unlink(missing_ok=True)

    audit(root)

    props = root / 'gradle.properties'
    text = props.read_text(encoding='utf-8')
    if 'mod_version=0.1.67-dev' in text:
        text = text.replace('mod_version=0.1.67-dev', 'mod_version=0.1.68-dev', 1)
    elif 'mod_version=0.1.68-dev' not in text:
        raise SystemExit('unexpected Veilbound version while finalizing 0.1.68')
    props.write_text(text, encoding='utf-8')
    print(f'VEILBOUND_0168_RECONSTRUCTION=PASS patch={patch_source} deterministic_assets=PASS version=0.1.68-dev')


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        traceback.print_exc(file=sys.stdout)
        raise
