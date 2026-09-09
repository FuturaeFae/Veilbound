from pathlib import Path
import json, math, struct, sys, zlib

root = Path(sys.argv[1]).resolve()
res = root / 'src/main/resources/assets/veilbound'
item_dir = res / 'textures/item'
block_dir = res / 'textures/block'
model_dir = res / 'models/block'

PNG_SIG = b'\x89PNG\r\n\x1a\n'


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def decode_rgba(path):
    data = path.read_bytes()
    if data[:8] != PNG_SIG:
        raise SystemExit(f'not a PNG: {path}')
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
        raise SystemExit(f'expected RGBA8 PNG: {path.name}')
    raw = zlib.decompress(b''.join(idat))
    stride = width * 4
    rows, off, prev = [], 0, bytearray(stride)
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
                raise SystemExit(f'unsupported PNG filter {filt}: {path.name}')
            out[i] = v
        rows.append(bytes(out))
        prev = out
    return width, height, rows


def chunk(typ, body):
    return struct.pack('>I', len(body)) + typ + body + struct.pack('>I', zlib.crc32(typ + body) & 0xffffffff)


def write_rgba(path, width, height, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = b''.join(b'\x00' + bytes(row) for row in rows)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    path.write_bytes(PNG_SIG + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def pixel(row, x):
    i = x * 4
    return tuple(row[i:i + 4])


def set_pixel(row, x, rgba):
    i = x * 4
    row[i:i + 4] = bytes(rgba)


def normalize_32(path, opaque=False, microdetail=False):
    w, h, rows = decode_rgba(path)
    if w <= 0 or h <= 0 or h % w != 0:
        raise SystemExit(f'non-square-frame texture cannot be normalized: {path.name} {w}x{h}')
    frames = h // w
    target_w = 32
    target_h = frames * target_w
    out_rows = []
    for ty in range(target_h):
        sy = min(h - 1, int(ty * h / target_h))
        row = bytearray(target_w * 4)
        for tx in range(target_w):
            sx = min(w - 1, int(tx * w / target_w))
            r, g, b, a = pixel(rows[sy], sx)
            if microdetail and a:
                # Add true 32 px material detail instead of leaving every 2x2 source pixel identical.
                jitter = ((tx * 17 + ty * 31 + (tx ^ ty) * 7) % 9) - 4
                if (tx + ty) & 1:
                    r = max(0, min(255, r + jitter))
                    g = max(0, min(255, g + jitter))
                    b = max(0, min(255, b + jitter))
            if opaque:
                a = 255
            set_pixel(row, tx, (r, g, b, a))
        out_rows.append(row)
    write_rgba(path, target_w, target_h, out_rows)


# Raise every native Veilbound sprite to 32 px per frame. Items receive a small deterministic
# second-order detail pass; block pixels remain opaque as required by the current material pass.
for p in sorted(item_dir.glob('*.png')):
    normalize_32(p, opaque=False, microdetail=True)
for p in sorted(block_dir.glob('*.png')):
    normalize_32(p, opaque=True, microdetail=True)


def is_colorful(rgba):
    r, g, b, _ = rgba
    return max(r, g, b) > 60 and max(r, g, b) - min(r, g, b) >= 28


# Force exact dimensional-resource silhouette parity between stone and deepslate while retaining
# each host's own grayscale texture. The colorful stone overlay is the canonical resource mask.
stone_path = block_dir / 'dimensional_shard_ore.png'
deep_path = block_dir / 'deepslate_dimensional_shard_ore.png'
sw, sh, srows = decode_rgba(stone_path)
dw, dh, drows = decode_rgba(deep_path)
if (sw, sh) != (32, 256) or (dw, dh) != (32, 256):
    raise SystemExit('dimensional ore sheets must be 32x256 before parity pass')
fixed_deep = []
for y in range(sh):
    dr = bytearray(drows[y])
    for x in range(sw):
        sp = pixel(srows[y], x)
        dp = pixel(drows[y], x)
        if is_colorful(sp):
            # Same prismatic vein pixel and therefore exactly the same colorful mask.
            set_pixel(dr, x, (sp[0], sp[1], sp[2], 255))
        elif is_colorful(dp):
            # Remove any old deepslate-only vein without inventing a new host color.
            luma = int(dp[0] * 0.2126 + dp[1] * 0.7152 + dp[2] * 0.0722)
            set_pixel(dr, x, (luma, luma, luma, 255))
        else:
            set_pixel(dr, x, (dp[0], dp[1], dp[2], 255))
    fixed_deep.append(dr)
write_rgba(deep_path, 32, 256, fixed_deep)


def refine_accretion(name, accent):
    path = block_dir / f'{name}.png'
    w, h, rows = decode_rgba(path)
    if (w, h) != (32, 256):
        raise SystemExit(f'{name} must be 32x256')
    out = [bytearray(r) for r in rows]
    frames = 8
    for frame in range(frames):
        oy = frame * 32
        phase = frame * 0.72
        # A void-implanted curved seam runs through the host block rather than looking like a flat recolor.
        for y in range(32):
            cx = 15.5 + math.sin(y * 0.33 + phase) * 5.1
            for x in range(32):
                d = abs(x - cx)
                idx_y = oy + y
                r, g, b, _ = pixel(out[idx_y], x)
                if d < 1.15:
                    set_pixel(out[idx_y], x, (4, 3, 8, 255))
                elif d < 2.2 and ((x + y + frame) % 3 != 0):
                    mix = 0.60
                    nr = int(r * (1 - mix) + accent[0] * mix)
                    ng = int(g * (1 - mix) + accent[1] * mix)
                    nb = int(b * (1 - mix) + accent[2] * mix)
                    set_pixel(out[idx_y], x, (nr, ng, nb, 255))
    write_rgba(path, 32, 256, out)


refine_accretion('resonant_accretion', (168, 92, 255))
refine_accretion('phase_accretion', (84, 226, 255))
refine_accretion('causal_accretion', (255, 130, 72))


def make_sheet(frame_fn, frames=4):
    rows = []
    for frame in range(frames):
        for y in range(32):
            row = bytearray(32 * 4)
            for x in range(32):
                set_pixel(row, x, frame_fn(frame, x, y))
            rows.append(row)
    return rows


def dyn_front(frame, x, y):
    # Furnace-derived iron/copper machine face with an animated boundary-energy aperture.
    edge = min(x, y, 31 - x, 31 - y)
    noise = ((x * 11 + y * 23 + frame * 7) % 13) - 6
    base = 62 + noise
    r = g = b = base
    if edge <= 2:
        r, g, b = 40 + noise, 43 + noise, 48 + noise
    if 5 <= x <= 26 and 5 <= y <= 25:
        r, g, b = 36 + noise, 39 + noise, 44 + noise
    copper = ((x in (6, 7, 24, 25) and 7 <= y <= 23) or (y in (7, 8, 22, 23) and 7 <= x <= 24))
    if copper:
        r, g, b = 151 + noise, 74 + noise // 2, 39
    if 11 <= x <= 20 and 12 <= y <= 19:
        pulse = (frame * 19 + (x - 11) * 7 + (y - 12) * 5) % 68
        r, g, b = 128 + pulse, 45 + pulse // 2, 28 + pulse // 4
    if (x, y) in ((4, 4), (27, 4), (4, 27), (27, 27)):
        r, g, b = 185, 188, 194
    return max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)), 255


def dyn_side(_frame, x, y):
    edge = min(x, y, 31 - x, 31 - y)
    n = ((x * 19 + y * 7) % 11) - 5
    if edge <= 2:
        return 42 + n, 45 + n, 50 + n, 255
    if (x // 4 + y // 4) % 4 == 0:
        return 115 + n, 62 + n // 2, 40, 255
    return 68 + n, 71 + n, 76 + n, 255


def dyn_top(_frame, x, y):
    d = abs(x - 15.5) + abs(y - 15.5)
    n = ((x * 13 + y * 29) % 9) - 4
    if 8 < d < 15:
        return 136 + n, 69 + n // 2, 40, 255
    return 70 + n, 73 + n, 79 + n, 255


write_rgba(block_dir / 'dynamo_front.png', 32, 128, make_sheet(dyn_front, 4))
write_rgba(block_dir / 'dynamo_side.png', 32, 32, make_sheet(dyn_side, 1))
write_rgba(block_dir / 'dynamo_top.png', 32, 32, make_sheet(dyn_top, 1))
(block_dir / 'dynamo_front.png.mcmeta').write_text(json.dumps({'animation': {'frametime': 3, 'interpolate': True}}, indent=2) + '\n', encoding='utf-8')


def anchor_pixel(face, frame, x, y):
    # Opaque void stone carrying a rotating internal prismatic current; in-world wisps are added by the block tick.
    cx = cy = 15.5
    dx, dy = x - cx, y - cy
    rad = math.hypot(dx, dy)
    ang = math.atan2(dy, dx)
    swirl = math.sin(ang * 3.0 + rad * 0.62 - frame * 1.35)
    grain = ((x * 37 + y * 17 + frame * 13 + len(face) * 5) % 17) - 8
    base = 13 + max(-4, grain // 2)
    r, g, b = base + 4, base, base + 9
    seam = abs(swirl) > 0.91 and 4.0 < rad < 14.5
    if seam:
        t = (ang / (2 * math.pi) + frame / 4.0) % 1.0
        r = int(74 + 115 * abs(math.sin(t * math.pi * 2)))
        g = int(45 + 88 * abs(math.sin((t + 0.33) * math.pi * 2)))
        b = int(116 + 122 * abs(math.sin((t + 0.66) * math.pi * 2)))
    if face == 'top' and rad < 3.2:
        pulse = 115 + frame * 22
        r, g, b = pulse, 80 + frame * 18, 210
    if face == 'bottom':
        r, g, b = int(r * 0.67), int(g * 0.67), int(b * 0.67)
    return max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)), 255


for face in ('side', 'top', 'bottom'):
    write_rgba(block_dir / f'void_anchor_{face}.png', 32, 128,
               make_sheet(lambda f, x, y, face=face: anchor_pixel(face, f, x, y), 4))
    (block_dir / f'void_anchor_{face}.png.mcmeta').write_text(
        json.dumps({'animation': {'frametime': 4, 'interpolate': True}}, indent=2) + '\n', encoding='utf-8')

# Solid, no-gap transducer geometry. Tier identity remains in the existing casing/panel/core textures.
for tier in ('dimensional', 'resonant', 'phase', 'causal'):
    model = {
        'parent': 'minecraft:block/block',
        'ambientocclusion': True,
        'textures': {
            'particle': f'veilbound:block/{tier}_transducer_casing',
            'casing': f'veilbound:block/{tier}_transducer_casing',
            'panel': f'veilbound:block/{tier}_transducer_panel',
            'core': f'veilbound:block/{tier}_transducer_core',
        },
        'elements': [{
            'from': [0, 0, 0], 'to': [16, 16, 16],
            'faces': {
                'down': {'texture': '#casing', 'cullface': 'down'},
                'up': {'texture': '#core', 'cullface': 'up'},
                'north': {'texture': '#panel', 'cullface': 'north'},
                'south': {'texture': '#panel', 'cullface': 'south'},
                'west': {'texture': '#panel', 'cullface': 'west'},
                'east': {'texture': '#panel', 'cullface': 'east'},
            }
        }]
    }
    (model_dir / f'{tier}_transducer.json').write_text(json.dumps(model, indent=2) + '\n', encoding='utf-8')

(model_dir / 'boundary_dynamo.json').write_text(json.dumps({
    'parent': 'minecraft:block/orientable',
    'textures': {
        'front': 'veilbound:block/dynamo_front',
        'side': 'veilbound:block/dynamo_side',
        'top': 'veilbound:block/dynamo_top'
    }
}, indent=2) + '\n', encoding='utf-8')

(model_dir / 'void_anchor.json').write_text(json.dumps({
    'parent': 'minecraft:block/cube_bottom_top',
    'textures': {
        'side': 'veilbound:block/void_anchor_side',
        'top': 'veilbound:block/void_anchor_top',
        'bottom': 'veilbound:block/void_anchor_bottom'
    }
}, indent=2) + '\n', encoding='utf-8')

print('VEILBOUND_0168_ASSET_GENERATION=PASS items=32px blocks=32px ores=parity transducers=solid dynamo=animated void_anchor=animated')
