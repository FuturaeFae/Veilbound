from pathlib import Path
import base64, hashlib, shutil, sys, tarfile

root = Path(sys.argv[1]).resolve()
ci = Path(__file__).resolve().parent
chunks = sorted((ci / 'chunks').glob('part*'))
if len(chunks) != 13:
    raise SystemExit(f'expected 13 overlay chunks, found {len(chunks)}')
encoded = ''.join(p.read_text(encoding='ascii').strip() for p in chunks)
payload = base64.b64decode(encoded, validate=True)
expected = 'c5a20c6846dde49539ea8287fa81531bed80b9f2bb413b84e1505ce8ddec4dc1'
actual = hashlib.sha256(payload).hexdigest()
if actual != expected:
    raise SystemExit(f'overlay checksum mismatch: {actual}')

# The first release intentionally removes the former large resource surface rather than leaving
# hidden recipes/assets/tags in the JAR. Recreate only the compact namespaces from the overlay.
for rel in [
    'src/main/resources/assets/veilbound',
    'src/main/resources/data/veilbound',
    'src/main/resources/data/c',
    'src/main/resources/data/minecraft/tags/block',
]:
    target = root / rel
    if target.is_dir(): shutil.rmtree(target)
    elif target.exists(): target.unlink()

tmp = ci / 'overlay-0166.tar.xz'
tmp.write_bytes(payload)
with tarfile.open(tmp, 'r:xz') as tf:
    for member in tf.getmembers():
        dest = (root / member.name).resolve()
        if root not in dest.parents and dest != root:
            raise SystemExit(f'unsafe overlay path: {member.name}')
    tf.extractall(root)
tmp.unlink()

# Compiler hardening for the slim cut: keep the new Core packet valid on MC 26.2 and physically
# remove the obsolete Boundary Pylon coordinator instead of retaining a dead compatibility shim.
snapshot = root / 'src/main/java/dev/futurae/veilbound/network/DomainControlsSnapshotPayload.java'
text = snapshot.read_text(encoding='utf-8')
method = '    @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }\n\n'
needle = '    public static DomainControlsSnapshotPayload denied(View view, String reason) {'
if method.strip() not in text:
    if needle not in text:
        raise SystemExit('could not locate DomainControlsSnapshotPayload insertion point')
    text = text.replace(needle, method + needle, 1)
    snapshot.write_text(text, encoding='utf-8')

pylon = root / 'src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeBoundaryPylonCoordinator.java'
if pylon.exists():
    pylon.unlink()

print(f'VEILBOUND_0166_APPLY=PASS chunks={len(chunks)} sha256={actual} packet_type=restored pylon_coordinator=removed')
