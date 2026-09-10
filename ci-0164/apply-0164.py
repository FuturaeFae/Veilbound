from pathlib import Path
import sys, tarfile, hashlib, json

root = Path(sys.argv[1]).resolve()
base = Path(__file__).parent / "bin"
parts = [
    "part00", "part01", "part02", "part03", "part04", "part05", "part06",
    "part0708", "part0910", "part1112", "part1314", "part1516",
    "part1718", "part1920", "part2122", "part2324", "part2526",
]
data = b"".join((base / name).read_bytes() for name in parts)
expected = "4989b2adc6e19d88d21bdda50fd96d5fb7ff4a89d6a2bcf282e241632c2a4162"
actual = hashlib.sha256(data).hexdigest()
if actual != expected:
    raise SystemExit(f"overlay checksum mismatch: {actual} != {expected}")
overlay = Path(__file__).with_name("overlay-0164.reconstructed.tar.xz")
overlay.write_bytes(data)
with tarfile.open(overlay, "r:xz") as tf:
    for member in tf.getmembers():
        dest = (root / member.name).resolve()
        if root not in dest.parents and dest != root:
            raise SystemExit(f"unsafe path: {member.name}")
    tf.extractall(root)

# Make the intended pre-Core workflow unambiguous in the actual shipped GUI text.
lang_path = root / "src/main/resources/assets/veilbound/lang/en_us.json"
lang = json.loads(lang_path.read_text(encoding="utf-8"))
lang["screen.veilbound.spatial_generator.mode.outside"] = (
    "Outside-Domain preparation mode — charge/condense here, then enter your Domain to expand."
)
lang_path.write_text(json.dumps(lang, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Matter tooltips use vanilla chat Components; keep the import explicit in the final source.
client_path = root / "src/main/java/dev/futurae/veilbound/client/VeilboundClient.java"
client = client_path.read_text(encoding="utf-8")
component_import = "import net.minecraft.network.chat.Component;\n"
if component_import not in client:
    anchor = "import net.minecraft.client.KeyMapping;\n"
    if anchor not in client:
        raise SystemExit("VeilboundClient import anchor missing")
    client = client.replace(anchor, component_import + anchor, 1)
client_path.write_text(client, encoding="utf-8")
