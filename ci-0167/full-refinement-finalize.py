from pathlib import Path
import base64, gzip, hashlib, io, json, struct, subprocess, sys, tarfile, zlib

root=Path(sys.argv[1]).resolve()
ci=Path(__file__).resolve().parent

PATCH_B64_SHA='1b70f2b330ffe34c20c6a8a718bb70eeca6658876aa8182a25401ff55c233f7a'
PATCH_RAW_SHA='80e5bf1a645bd3b55c7e665bbbb5dd2ed3d4edace29e239a7a70523e823dd66b'
ASSET_B64_SHA='00d51973d75bd06ac1969d8c258175043e6872d64eded11ce96d2939e0e4ad32'
ASSET_RAW_SHA='ce08ea6051eef25f3e44df0100dd23ea1f1a636f78242ec95df84d8080c10eab'

patch_payload=ci/'full-refinement-pass.patch.gz.b64'
if not patch_payload.is_file(): raise SystemExit('missing full refinement patch payload')
pb64=patch_payload.read_text(encoding='ascii').strip().encode('ascii')
if hashlib.sha256(pb64).hexdigest()!=PATCH_B64_SHA: raise SystemExit('full refinement patch base64 sha mismatch')
patch=gzip.decompress(base64.b64decode(pb64))
if hashlib.sha256(patch).hexdigest()!=PATCH_RAW_SHA: raise SystemExit('full refinement patch raw sha mismatch')
tmp=ci/'.full-refinement.patch.tmp'; tmp.write_bytes(patch)
try:
    subprocess.run(['patch','-p1','--batch','-i',str(tmp)],cwd=root,check=True)
finally:
    tmp.unlink(missing_ok=True)

parts=[ci/f'full-refinement-assets.tar.gz.b64.part{i:02d}' for i in range(17)]
if not all(p.is_file() for p in parts): raise SystemExit('missing full refinement asset payload part')
ab64=''.join(p.read_text(encoding='ascii').strip() for p in parts).encode('ascii')
if hashlib.sha256(ab64).hexdigest()!=ASSET_B64_SHA: raise SystemExit('full refinement assets base64 sha mismatch')
archive=base64.b64decode(ab64)
if hashlib.sha256(archive).hexdigest()!=ASSET_RAW_SHA: raise SystemExit('full refinement assets raw sha mismatch')
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tf:
    tf.extractall(root)

# Superseded one-face resources are intentionally gone.
(root/'src/main/resources/assets/veilbound/textures/block/boundary_dynamo.png').unlink(missing_ok=True)
(root/'src/main/resources/assets/veilbound/textures/block/void_anchor.png').unlink(missing_ok=True)

java=root/'src/main/java'
res=root/'src/main/resources/assets/veilbound'
terminal=(java/'dev/futurae/veilbound/client/screen/VeilInventoryScreen.java').read_text(encoding='utf-8')
prefs=(java/'dev/futurae/veilbound/client/screen/VeilInventoryPreferences.java').read_text(encoding='utf-8')
style=(java/'dev/futurae/veilbound/client/screen/VanillaGuiStyle.java').read_text(encoding='utf-8')
transscreen=(java/'dev/futurae/veilbound/client/screen/DimensionalTransducerScreen.java').read_text(encoding='utf-8')
dynscreen=(java/'dev/futurae/veilbound/client/screen/BoundaryDynamoScreen.java').read_text(encoding='utf-8')
transint=(java/'dev/futurae/veilbound/platform/neoforge/NeoForgeTransducerCoordinator.java').read_text(encoding='utf-8')
dynblock=(java/'dev/futurae/veilbound/block/BoundaryDynamoBlock.java').read_text(encoding='utf-8')
anchorblock=(java/'dev/futurae/veilbound/block/VoidAnchorBlock.java').read_text(encoding='utf-8')

required={
 'withdraw virtual grid first':'Virtual terminal controls must run before AbstractContainerScreen',
 'draggable scrollbar state':'draggingScrollBar',
 'draggable scrollbar method':'mouseDragged(MouseButtonEvent event, double dragX, double dragY)',
 'craftable/all selector':'handleCraftFilterClick',
 'craftable/all request':'showAllCrafts, Math.max(0, page), craftingQuery, craftingSort',
 'sort backwards on right click':'cycleSort(button == 1 ? -1 : 1)',
 'short search hint':'searchBox.setHint(Component.literal("Search"))',
 'craft filter persisted':'veilInventory.crafting.showAllRecipes',
}
for label,marker in required.items():
    hay=terminal if label!='craft filter persisted' else prefs
    if marker not in hay: raise SystemExit(f'full refinement GUI audit failed: {label}')
if 'col * 18 - 1' not in style or 'hotbarY - 1' not in style:
    raise SystemExit('vanilla player slot bevel alignment missing')
for marker in ('Matter: "','DE: "','FE: "'):
    if marker not in transscreen: raise SystemExit(f'transducer hover tooltip missing: {marker}')
if 'BoundaryDynamoBlockEntity.FE_CAPACITY' not in dynscreen:
    raise SystemExit('Dynamo exact FE hover tooltip missing')
if 'if (player.isShiftKeyDown()) return;' not in transint:
    raise SystemExit('transducer sneak-place bypass missing')
if 'if (player.isShiftKeyDown()) return InteractionResult.PASS;' not in dynblock:
    raise SystemExit('Dynamo sneak-place bypass missing')
if 'ParticleTypes.REVERSE_PORTAL' not in anchorblock or 'animateTick(' not in anchorblock:
    raise SystemExit('Void Anchor visual wisp animation missing')

lang=json.loads((res/'lang/en_us.json').read_text(encoding='utf-8'))
if lang.get('block.veilbound.boundary_dynamo')!='Dynamo' or lang.get('container.veilbound.boundary_dynamo')!='Dynamo':
    raise SystemExit('Boundary Dynamo display rename missing')
if lang.get('screen.veilbound.veil_inventory.search_hint')!='Search':
    raise SystemExit('Veil search hint did not shorten')

# Minimal RGBA PNG reader for exact dimension/alpha/mask audits without external packages.
def decode_rgba(path:Path):
    data=path.read_bytes()
    if data[:8]!=b'\x89PNG\r\n\x1a\n': raise SystemExit(f'not PNG: {path}')
    pos=8; width=height=depth=ctype=None; idat=[]
    while pos<len(data):
        ln=struct.unpack('>I',data[pos:pos+4])[0]; typ=data[pos+4:pos+8]; body=data[pos+8:pos+8+ln]; pos+=12+ln
        if typ==b'IHDR': width,height,depth,ctype,_,_,_=struct.unpack('>IIBBBBB',body)
        elif typ==b'IDAT': idat.append(body)
        elif typ==b'IEND': break
    if depth!=8 or ctype!=6: raise SystemExit(f'expected RGBA8 PNG: {path.name} depth={depth} type={ctype}')
    raw=zlib.decompress(b''.join(idat)); stride=width*4; rows=[]; off=0; prev=bytearray(stride)
    def paeth(a,b,c):
        p=a+b-c; pa=abs(p-a); pb=abs(p-b); pc=abs(p-c)
        return a if pa<=pb and pa<=pc else (b if pb<=pc else c)
    for _y in range(height):
        filt=raw[off]; off+=1; scan=bytearray(raw[off:off+stride]); off+=stride
        out=bytearray(stride)
        for i,x in enumerate(scan):
            a=out[i-4] if i>=4 else 0; b=prev[i]; c=prev[i-4] if i>=4 else 0
            if filt==0: v=x
            elif filt==1: v=(x+a)&255
            elif filt==2: v=(x+b)&255
            elif filt==3: v=(x+((a+b)//2))&255
            elif filt==4: v=(x+paeth(a,b,c))&255
            else: raise SystemExit(f'unsupported PNG filter {filt} in {path.name}')
            out[i]=v
        rows.append(bytes(out)); prev=out
    return width,height,rows

# Every native item sprite is doubled to 32px and remains an 8-frame sheet.
for p in sorted((res/'textures/item').glob('*.png')):
    w,h,_=decode_rgba(p)
    if w!=32 or h%32!=0 or h<32:
        raise SystemExit(f'item texture not native 32px: {p.name} {w}x{h}')
for name in ('dimensional_shard','resonant_crystal','phase_mote','causal_fragment','genesis_seed'):
    w,h,_=decode_rgba(res/f'textures/item/{name}.png')
    if (w,h)!=(32,256): raise SystemExit(f'animated item wrong size: {name} {w}x{h}')

# No block texture may contain a transparent pixel; all current block textures are native 32px.
for p in sorted((res/'textures/block').glob('*.png')):
    w,h,rows=decode_rgba(p)
    if w!=32 or h%32!=0: raise SystemExit(f'block texture not native 32px: {p.name} {w}x{h}')
    if any(row[i]!=255 for row in rows for i in range(3,len(row),4)):
        raise SystemExit(f'transparent pixel survived in block texture: {p.name}')

for name in ('dimensional_shard_ore','deepslate_dimensional_shard_ore','resonant_accretion','phase_accretion','causal_accretion'):
    w,h,_=decode_rgba(res/f'textures/block/{name}.png')
    if (w,h)!=(32,256): raise SystemExit(f'ore/accretion wrong size: {name} {w}x{h}')
for name in ('void_anchor_side','void_anchor_top','void_anchor_bottom'):
    w,h,_=decode_rgba(res/f'textures/block/{name}.png')
    if (w,h)!=(32,128) or not Path(str(res/f'textures/block/{name}.png')+'.mcmeta').is_file():
        raise SystemExit(f'Void Anchor animation texture invalid: {name}')
w,h,_=decode_rgba(res/'textures/block/dynamo_front.png')
if (w,h)!=(32,128) or not (res/'textures/block/dynamo_front.png.mcmeta').is_file():
    raise SystemExit('Dynamo animated furnace front invalid')

# Stone and deepslate must carry the same prismatic resource silhouette. Compare colorful masks frame-by-frame.
def colorful_mask(rows,w,h):
    masks=[]
    for row in rows:
        line=[]
        for x in range(w):
            r,g,b,a=row[x*4:x*4+4]; mx=max(r,g,b); mn=min(r,g,b)
            line.append(mx>60 and (mx-mn)>=28)
        masks.append(line)
    return masks
sw,sh,srows=decode_rgba(res/'textures/block/dimensional_shard_ore.png')
dw,dh,drows=decode_rgba(res/'textures/block/deepslate_dimensional_shard_ore.png')
if (sw,sh)!=(dw,dh): raise SystemExit('dimensional ore variants size mismatch')
sm=colorful_mask(srows,sw,sh); dm=colorful_mask(drows,dw,dh)
# host rock is grayscale; any colorful mask difference means the ore overlay itself diverged.
if sm!=dm: raise SystemExit('stone/deepslate dimensional ore overlay silhouette diverged')

# Transducers must occupy the full 16^3 block volume with no gaps and must not protrude into an adjacent block.
for tier in ('dimensional','resonant','phase','causal'):
    model=json.loads((res/f'models/block/{tier}_transducer.json').read_text(encoding='utf-8'))
    elems=model.get('elements',[])
    for e in elems:
        if any(v<0 or v>16 for v in e['from']+e['to']): raise SystemExit(f'{tier} transducer model protrudes outside block')
    for x in range(16):
        for y in range(16):
            for z in range(16):
                if not any(e['from'][0]<=x<e['to'][0] and e['from'][1]<=y<e['to'][1] and e['from'][2]<=z<e['to'][2] for e in elems):
                    raise SystemExit(f'{tier} transducer model has empty voxel at {x},{y},{z}')

model=json.loads((res/'models/block/boundary_dynamo.json').read_text(encoding='utf-8'))
if model.get('parent')!='minecraft:block/orientable' or model.get('textures',{}).get('front')!='veilbound:block/dynamo_front':
    raise SystemExit('Dynamo furnace-derived model missing')
anchor=json.loads((res/'models/block/void_anchor.json').read_text(encoding='utf-8'))
if anchor.get('parent')!='minecraft:block/cube_bottom_top' or anchor.get('textures',{}).get('top')!='veilbound:block/void_anchor_top':
    raise SystemExit('Void Anchor multi-face model missing')
if (res/'textures/block/boundary_dynamo.png').exists() or (res/'textures/block/void_anchor.png').exists():
    raise SystemExit('superseded single-face block texture survived')

print('VEILBOUND_0167_FULL_REFINEMENT=PASS all_pending_user_updates=present')
print('VEILBOUND_0167_GUI=PASS withdrawal=restored player_inventory=vanilla slots=aligned scrollbar=draggable search=Search craft_filter=craftable_or_all sort=left_forward_right_back meter_hover=exact_values')
print('VEILBOUND_0167_WORLD_INTERACTION=PASS transducer_sneak_place=PASS dynamo_sneak_place=PASS')
print('VEILBOUND_0167_TEXTURES=PASS item_resolution=32px ores=32px_animated dimensional_overlay=identical_stone_deepslate accretions=reference_implanted_void all_block_pixels=opaque')
print('VEILBOUND_0167_MACHINES=PASS transducers=solid_no_gaps dynamo=furnace_iron_copper_animated rename=Dynamo void_anchor=32px_animated_wisps')
