from __future__ import annotations

import base64
import hashlib
import itertools
from pathlib import Path

EXPECTED_SHA256 = "d4d6832d55ab959915a736a9c2539874feeb5eebb2572a166f4aa413613f5dab"
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def clean_part(path: Path) -> str:
    allowed = set(ALPHABET + "=")
    return "".join(ch for ch in path.read_text(encoding="ascii") if ch in allowed)


def decoded_if_match(text: str) -> bytes | None:
    try:
        raw = base64.b64decode(text, validate=True)
    except Exception:
        return None
    if hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256:
        return raw
    return None


def main() -> None:
    ci = Path(__file__).resolve().parent
    parts = sorted(ci.glob("ref-assets-v2.part*"))
    if len(parts) != 9:
        raise SystemExit(f"expected 9 reference asset chunks, found {[p.name for p in parts]}")

    chunks = [clean_part(p) for p in parts]
    print("VEILBOUND_0169_REF_PART_LENGTHS=" + ",".join(str(len(x)) for x in chunks))

    joined = "".join(chunks)
    direct = decoded_if_match(joined)
    if direct is not None:
        Path("veil169-reference-assets.tar.gz").write_bytes(direct)
        print("VEILBOUND_0169_REFERENCE_ASSETS=PASS recovery=none sha256=" + EXPECTED_SHA256)
        return

    # part06 is exactly two characters shorter than the intended 9000-character chunk while
    # surrounding full chunks are exactly 9000. The original split therefore dropped two base64
    # symbols at that boundary. Recover those two symbols exhaustively and accept only the payload
    # whose decoded bytes match the SHA-256 recorded when the reference asset tarball was created.
    short_index = 6
    if len(chunks[short_index]) != 8998:
        raise SystemExit(f"unexpected short chunk length: part06={len(chunks[short_index])}")

    boundary_after = sum(len(c) for c in chunks[: short_index + 1])
    boundary_before = sum(len(c) for c in chunks[:short_index])

    # Primary expected location: the missing symbols were the final two chars of part06. Keep a
    # beginning-of-part06 fallback for resilience, but do not guess beyond the uniquely short chunk.
    sites = [("after_part06", boundary_after), ("before_part06", boundary_before)]
    for label, pos in sites:
        prefix, suffix = joined[:pos], joined[pos:]
        for a, b in itertools.product(ALPHABET, repeat=2):
            raw = decoded_if_match(prefix + a + b + suffix)
            if raw is None:
                continue
            Path("veil169-reference-assets.tar.gz").write_bytes(raw)
            print(
                "VEILBOUND_0169_REFERENCE_ASSETS=PASS recovery="
                + label
                + " inserted="
                + a
                + b
                + " sha256="
                + EXPECTED_SHA256
            )
            return

    raise SystemExit("unable to recover the two missing reference-asset base64 symbols at part06 boundary")


if __name__ == "__main__":
    main()
