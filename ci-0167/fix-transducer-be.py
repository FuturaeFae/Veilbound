from pathlib import Path
import base64
import gzip
import hashlib
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
print(f'VEILBOUND_0167_TRANSDUCER_BE_FIX=PASS sha256={sha} bytes={len(raw)}')
