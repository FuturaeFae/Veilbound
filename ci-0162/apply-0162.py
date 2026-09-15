#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys, tarfile

EXPECTED_SHA256 = '3ba1543a69ac7c79028443051f20d23d530ce8b4a13bc8264c3d6a325efc0a5f'

if len(sys.argv) != 2:
    raise SystemExit('usage: apply-0162.py <source-root>')
source = Path(sys.argv[1]).resolve()
archive = Path(__file__).resolve().parent / 'overlay-0162.tar.xz'
if not source.is_dir() or not archive.is_file():
    raise SystemExit('missing source or overlay archive')
actual = hashlib.sha256(archive.read_bytes()).hexdigest()
if actual != EXPECTED_SHA256:
    raise SystemExit(f'overlay digest mismatch: {actual}')
with tarfile.open(archive, mode='r:xz') as tf:
    members = tf.getmembers()
    for member in members:
        target = (source / member.name).resolve()
        if source != target and source not in target.parents:
            raise SystemExit(f'unsafe overlay member: {member.name}')
    tf.extractall(source, members=members, filter='data')
print(f'VEILBOUND_0162_OVERLAY_SHA256={actual}')
print(f'VEILBOUND_0162_OVERLAY_FILES={sum(1 for m in members if m.isfile())}')
