from pathlib import Path
import sys, tarfile
root = Path(sys.argv[1]).resolve()
overlay = Path(__file__).with_name('overlay-0163.tar.xz')
with tarfile.open(overlay, 'r:xz') as tf:
    for member in tf.getmembers():
        dest = (root / member.name).resolve()
        if root not in dest.parents and dest != root:
            raise SystemExit(f'unsafe path: {member.name}')
    tf.extractall(root)
