from pathlib import Path
import base64, hashlib, io, sys, tarfile

root = Path(sys.argv[1]).resolve()
ci_dir = Path(__file__).resolve().parent
parts = sorted(ci_dir.glob('overlay.part*.b64'))
if len(parts) != 5:
    raise SystemExit(f'expected 5 overlay chunks, found {len(parts)}')
encoded = ''.join(p.read_text(encoding='utf-8').strip() for p in parts)
data = base64.b64decode(encoded, validate=True)
digest = hashlib.sha256(data).hexdigest()
expected = '4989b2adc6e19d88d21bdda50fd96d5fb7ff4a89d6a2bcf282e241632c2a4162'
if digest != expected:
    raise SystemExit(f'overlay checksum mismatch: {digest} != {expected}')
with tarfile.open(fileobj=io.BytesIO(data), mode='r:xz') as tf:
    for member in tf.getmembers():
        dest = (root / member.name).resolve()
        if root not in dest.parents and dest != root:
            raise SystemExit(f'unsafe path: {member.name}')
    tf.extractall(root)
print(f'VEILBOUND_0164_OVERLAY=PASS sha256={digest} parts={len(parts)}')
