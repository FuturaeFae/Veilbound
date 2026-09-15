from pathlib import Path
import shutil, sys

root = Path(sys.argv[1]).resolve()
ci = Path(__file__).resolve().parent
copies = {
    'DimensionalTransducerMenu.java': 'src/main/java/dev/futurae/veilbound/menu/DimensionalTransducerMenu.java',
    'DimensionalTransducerScreen.java': 'src/main/java/dev/futurae/veilbound/client/screen/DimensionalTransducerScreen.java',
    'DimensionalTransducerBlockEntity.java': 'src/main/java/dev/futurae/veilbound/block/entity/DimensionalTransducerBlockEntity.java',
    'NeoForgeTransducerCoordinator.java': 'src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeTransducerCoordinator.java',
}
for src_name, dst_name in copies.items():
    src = ci / src_name
    dst = root / dst_name
    if not src.is_file():
        raise SystemExit(f'missing transducer source payload: {src_name}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
print('VEILBOUND_0167_TRANSDUCER_SOURCES=STAGED')
