from pathlib import Path
import json
import re
import sys

root = Path(sys.argv[1]).resolve()
java = root / 'src/main/java'
test = root / 'src/test/java'
res = root / 'src/main/resources'

# Boundary Pylons are not a current registered block. Remove the old out-of-bounds placement/break
# exceptions entirely; all new outside-boundary placement is forbidden. Keep only the owner cleanup
# exception for Void Anchors that an older build may already have stranded outside the usable bounds.
coordinator = java / 'dev/futurae/veilbound/platform/neoforge/NeoForgeVeilBoundaryCoordinator.java'
text = coordinator.read_text(encoding='utf-8')
text = text.replace('import dev.futurae.veilbound.domain.AxisDirection;\n', '')
text = text.replace('import dev.futurae.veilbound.domain.BoundaryPylonBindingService;\n', '')
text = text.replace(
    ' * blocks, entities, fluids, and piston movement may not cross them. Boundary Pylons are the sole\n'
    ' * block-placement exception and live one cell into the Veil on their assigned moving face.\n',
    ' * blocks, entities, fluids, and piston movement may not cross them.\n')
text = re.sub(
    r'\n        // The only legal block in the impassable Veil is the owner\'s Pylon at its exact face slot\.\n'
    r'        if \(event\.getPlacedBlock\(\)\.is\(VeilboundBlocks\.BOUNDARY_PYLON\.get\(\)\).*?\n'
    r'        \}\n'
    r'        event\.setCanceled\(true\);',
    '\n        event.setCanceled(true);', text, flags=re.S)
text = re.sub(
    r'\n        boolean ownerBoundPylon = .*?\n'
    r'                    \.anyMatch\(pylon -> pylon\.bound\(\) && pos\.equals\(pylon\.blockPosition\(\)\)\);',
    '', text, flags=re.S)
text = text.replace(
    '        if (!ownerBoundPylon && !ownerOrphanVoidAnchor) event.setCanceled(true);',
    '        if (!ownerOrphanVoidAnchor) event.setCanceled(true);')
coordinator.write_text(text, encoding='utf-8')

# Re-run reachability including package-private top-level types. The first pass removes the large
# public legacy clusters; this pass catches helpers that are not public and anything made unreachable
# by removing the last Boundary Pylon runtime branch above.
files = list(java.rglob('*.java'))
texts = {path: path.read_text(encoding='utf-8', errors='ignore') for path in files}
name_to_file = {}
file_to_name = {}
for path, source in texts.items():
    match = re.search(
        r'^(?:public\s+)?(?:final\s+|abstract\s+|sealed\s+)?(?:class|interface|record|enum)\s+(\w+)',
        source, flags=re.M)
    if match:
        name_to_file[match.group(1)] = path
        file_to_name[path] = match.group(1)

edges = {name: set() for name in name_to_file}
for path, source in texts.items():
    owner = file_to_name.get(path)
    if owner is None:
        continue
    for name, target in name_to_file.items():
        if target != path and re.search(r'\b' + re.escape(name) + r'\b', source):
            edges[owner].add(name)

roots = {
    'Veilbound', 'VeilboundClient', 'MinecraftServerAccessor',
    'EntityVeilBoundaryCollisionMixin', 'ClientLevelEnvironmentAccessor'
}
reachable = set(roots)
queue = list(roots)
while queue:
    owner = queue.pop()
    for target in edges.get(owner, ()):
        if target not in reachable:
            reachable.add(target)
            queue.append(target)

dead_types = {name for name in name_to_file if name not in reachable}
dead_files = {name_to_file[name] for name in dead_types}
for path in dead_files:
    if path.exists():
        path.unlink()

removed_tests = 0
if dead_types and test.exists():
    pattern = re.compile(
        r'\b(?:' + '|'.join(map(re.escape, sorted(dead_types, key=len, reverse=True))) + r')\b')
    for path in list(test.rglob('*.java')):
        if pattern.search(path.read_text(encoding='utf-8', errors='ignore')):
            path.unlink()
            removed_tests += 1

# Remove stale localization left by previous UI iterations. Keep exact runtime translation keys,
# automatic item/block names backed by current assets, the active key category, and the one dynamic
# Genesis Seed rejection key constructed from GenesisSeedService's reason string.
lang = res / 'assets/veilbound/lang/en_us.json'
translations = json.loads(lang.read_text(encoding='utf-8'))
all_source = '\n'.join(
    path.read_text(encoding='utf-8', errors='ignore') for path in java.rglob('*.java'))
used_keys = set()
for key in translations:
    if f'"{key}"' in all_source:
        used_keys.add(key)
    elif key in {'itemGroup.veilbound', 'key.category.veilbound.veilbound'}:
        used_keys.add(key)
    elif key.startswith('block.veilbound.'):
        identifier = key.split('.', 2)[2]
        if (res / 'assets/veilbound/blockstates' / f'{identifier}.json').is_file():
            used_keys.add(key)
    elif key.startswith('item.veilbound.'):
        identifier = key.split('.', 2)[2]
        if (res / 'assets/veilbound/items' / f'{identifier}.json').is_file():
            used_keys.add(key)
used_keys.add('message.veilbound.genesis_seed.domain_already_bound')
pruned = {key: value for key, value in translations.items() if key in used_keys}
lang.write_text(json.dumps(pruned, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

# Resource and build-hook sanity after deletion.
assets = res / 'assets/veilbound'
for path in (assets / 'blockstates').glob('*.json'):
    if not (assets / 'models/block' / path.name).is_file():
        raise SystemExit(f'missing active block model: {path.stem}')
for path in (assets / 'items').glob('*.json'):
    if not (assets / 'models/item' / path.name).is_file():
        raise SystemExit(f'missing active item model: {path.stem}')
for metadata in assets.rglob('*.png.mcmeta'):
    png = Path(str(metadata)[:-7])
    if not png.is_file():
        raise SystemExit(f'orphan animation metadata: {metadata.relative_to(assets)}')

build = (root / 'build.gradle').read_text(encoding='utf-8')
for fqcn in set(re.findall(r"'((?:dev\.)[^']+SelfTest)'", build)):
    source = test / Path(*fqcn.split('.')).with_suffix('.java')
    if not source.is_file():
        raise SystemExit(f'dangling Gradle self-test: {fqcn}')

all_java = '\n'.join(
    path.read_text(encoding='utf-8', errors='ignore') for path in java.rglob('*.java'))
for forbidden in (
    'BOUNDARY_PYLON.get()', 'BoundaryPylonBindingService', 'BreachLinkData',
    'EngineeringMonumentBlock', 'VeilLanceBlock', 'ThresholdPortalBlock',
    'VeilboundDataComponents', '@Deprecated public static final'):
    if forbidden in all_java:
        raise SystemExit(f'final cleanup incomplete: {forbidden}')

print(
    'VEILBOUND_0167_FINAL_CLEANUP=PASS '
    f'additional_main_removed={len(dead_files)} additional_tests_removed={removed_tests} '
    f'main_java={len(list(java.rglob("*.java")))} '
    f'lang_keys={len(pruned)} lang_removed={len(translations) - len(pruned)}')
