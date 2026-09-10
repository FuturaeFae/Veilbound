from pathlib import Path
import hashlib, json, sys

root = Path(sys.argv[1]).resolve()
ci = Path(__file__).resolve().parent


def replace_file(target, prefix, parts):
    data = ''.join((ci / 'fragments' / f'{prefix}.part{i:02d}').read_text(encoding='utf-8') for i in range(parts))
    path = root / target
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding='utf-8')

replace_file('src/main/java/dev/futurae/veilbound/client/screen/VeilInventoryScreen.java', 'VeilInventoryScreen', 4)
replace_file('src/main/java/dev/futurae/veilbound/platform/neoforge/inventory/NeoForgeVeilInventoryController.java', 'NeoForgeVeilInventoryController', 2)
replace_file('src/main/java/dev/futurae/veilbound/platform/neoforge/inventory/NeoForgeVeilCraftingController.java', 'NeoForgeVeilCraftingController', 2)
replace_file('src/main/java/dev/futurae/veilbound/platform/neoforge/inventory/NeoForgeVeilCraftablesController.java', 'NeoForgeVeilCraftablesController', 3)
replace_file('src/test/java/dev/futurae/veilbound/inventory/VeilInventorySelfTest.java', 'VeilInventorySelfTest', 1)

# Update legacy self-tests to the first-release unlimited Domain terminal policy.
for rel in [
    'src/test/java/dev/futurae/veilbound/inventory/VeilCraftingSelfTest.java',
    'src/test/java/dev/futurae/veilbound/inventory/VeilTransmutationSelfTest.java',
]:
    tp = root / rel
    tp.write_text(tp.read_text(encoding='utf-8').replace('VeilStoragePolicy.RESONANT', 'VeilStorageCapacity.EFFECTIVELY_UNLIMITED'), encoding='utf-8')

# First-release storage is Domain-owned immediately and has no upgrade/capacity gate.
(root / 'src/main/java/dev/futurae/veilbound/inventory/VeilStoragePolicy.java').write_text('''package dev.futurae.veilbound.inventory;\n\nimport dev.futurae.veilbound.domain.DomainState;\nimport java.util.Objects;\n\n/** First-release storage policy: every bound Domain owns an effectively-unlimited Veil terminal. */\npublic final class VeilStoragePolicy {\n    public VeilStorageCapacity capacityFor(DomainState state) {\n        Objects.requireNonNull(state, "state");\n        return VeilStorageCapacity.EFFECTIVELY_UNLIMITED;\n    }\n}\n''', encoding='utf-8')

# Matter transmutation is inherent to the Domain terminal.
p = root / 'src/main/java/dev/futurae/veilbound/matter/MatterTransmutationService.java'
s = p.read_text(encoding='utf-8').replace('import dev.futurae.veilbound.domain.DomainFeature;\n', '')
for line in [
    '        if (!state.hasFeature(DomainFeature.VEIL_TRANSMUTATION)) return LearnResult.denied("veil_transmutation_locked");\n',
    '        if (!state.hasFeature(DomainFeature.VEIL_TRANSMUTATION)) return AbsorbResult.denied("veil_transmutation_locked");\n',
    '        if (!state.hasFeature(DomainFeature.VEIL_TRANSMUTATION)) return SynthesisResult.denied("veil_transmutation_locked");\n',
    '        if (!state.hasFeature(DomainFeature.VEIL_TRANSMUTATION)) return MigrationResult.denied("veil_transmutation_locked");\n',
]:
    s = s.replace(line, '')
p.write_text(s, encoding='utf-8')

# Crafting is inherent too; if a Matter state is supplied it is always usable.
p = root / 'src/main/java/dev/futurae/veilbound/inventory/VeilCraftingService.java'
s = p.read_text(encoding='utf-8').replace('import dev.futurae.veilbound.domain.DomainFeature;\n', '')
s = s.replace('        if (!state.hasFeature(DomainFeature.VEIL_CRAFTING)) return CraftResult.denied("veil_crafting_locked");\n', '')
s = s.replace('        if (!state.hasFeature(DomainFeature.VEIL_TRANSMUTATION)) return CraftResult.denied("veil_transmutation_locked");\n', '')
s = s.replace('        boolean matterEnabled = transmutation != null && state.hasFeature(DomainFeature.VEIL_TRANSMUTATION);',
              '        boolean matterEnabled = transmutation != null;')
p.write_text(s, encoding='utf-8')

# Network surface changes.
p = root / 'src/main/java/dev/futurae/veilbound/network/VeilInventoryActionPayload.java'
s = p.read_text(encoding='utf-8').replace(
    '        DEPOSIT_HELD,\n        WITHDRAW_ONE,',
    '        DEPOSIT_HELD,\n        DEPOSIT_RESOURCE_ONE,\n        DEPOSIT_RESOURCE_STACK,\n        WITHDRAW_ONE,')
p.write_text(s, encoding='utf-8')

p = root / 'src/main/java/dev/futurae/veilbound/network/VeilInventorySnapshotPayload.java'
p.write_text(p.read_text(encoding='utf-8').replace(
    'public static final int MAX_NETWORK_ENTRIES = 45;',
    'public static final int MAX_NETWORK_ENTRIES = 90;'), encoding='utf-8')

p = root / 'src/main/java/dev/futurae/veilbound/network/VeilCraftablesSnapshotPayload.java'
p.write_text(p.read_text(encoding='utf-8').replace(
    'public static final int PAGE_SIZE = 36;',
    'public static final int PAGE_SIZE = 81;'), encoding='utf-8')

p = root / 'src/main/java/dev/futurae/veilbound/network/VeilCraftingRequestPayload.java'
p.write_text(p.read_text(encoding='utf-8').replace(
    '    public enum Action { PREVIEW, CRAFT_ONCE }',
    '    public enum Action { PREVIEW, CRAFT_ONCE, CRAFT_MAX }'), encoding='utf-8')

p = root / 'src/main/java/dev/futurae/veilbound/platform/neoforge/network/NeoForgeNetworking.java'
p.write_text(p.read_text(encoding='utf-8').replace('PROTOCOL = "18"', 'PROTOCOL = "19"'), encoding='utf-8')

p = root / 'gradle.properties'
p.write_text(p.read_text(encoding='utf-8').replace('mod_version=0.1.64-dev', 'mod_version=0.1.65-dev'), encoding='utf-8')

# GUI strings kept in the standard lang file, without shipping a giant replacement file in CI.
p = root / 'src/main/resources/assets/veilbound/lang/en_us.json'
data = json.loads(p.read_text(encoding='utf-8'))
data['screen.veilbound.veil_inventory.player_inventory'] = 'Inventory'
data['screen.veilbound.veil_inventory.crafting_locked'] = 'Crafting is available with your Domain.'
data['screen.veilbound.veil_inventory.transmutation_locked'] = 'Matter transmutation is available with your Domain.'
p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

expected = {
    'gradle.properties': 'fd85855c01d3f829120862e6778e34516706e02ae97891e5458977e475f044a8',
    'src/main/java/dev/futurae/veilbound/inventory/VeilStoragePolicy.java': 'ff7d4ccbf25f40e2ad7c9b6082d68d67da36cd0739404c09bc69f7d53c77a78c',
    'src/main/java/dev/futurae/veilbound/matter/MatterTransmutationService.java': '4ee59a92f74c2fdc7fb665c1c2bc2b8ef7748241252c9622a674dee531ab70b0',
    'src/main/java/dev/futurae/veilbound/inventory/VeilCraftingService.java': '49b50ec6d86b0b4f3429deb094ce8cb56da1e2ec5aec18f6259c440418621b29',
    'src/main/java/dev/futurae/veilbound/network/VeilInventoryActionPayload.java': 'fb073350f8d22e118a0f33bbd1b8d8aa9f5b3a3106fa3c39651e3a1cc407e908',
    'src/main/java/dev/futurae/veilbound/network/VeilInventorySnapshotPayload.java': 'd66eb363fb765100ef0e07d0dde7a1aaf35842a9bf0b2f03da22948b830f0c6c',
    'src/main/java/dev/futurae/veilbound/network/VeilCraftablesSnapshotPayload.java': '91716c99511d89d81fdc62c9d201e53d4c2ad6ce5729df11acc0de8c075d2bc2',
    'src/main/java/dev/futurae/veilbound/network/VeilCraftingRequestPayload.java': '5e24acf5e6238c782c4f4e8961f1c6b808b3a4cb32f7113969143376ad99a045',
    'src/main/java/dev/futurae/veilbound/platform/neoforge/inventory/NeoForgeVeilInventoryController.java': '76f1ca7e192b1c05ec2b278cdf8ee8b4ef326c168a98be0b50f76708ede1f1a4',
    'src/main/java/dev/futurae/veilbound/platform/neoforge/inventory/NeoForgeVeilCraftablesController.java': 'd91d93b6b68c516e8cc3025fa2d57884392f9761d9199b915eb0f1699750462c',
    'src/main/java/dev/futurae/veilbound/platform/neoforge/inventory/NeoForgeVeilCraftingController.java': 'd0db5a1dd910d29e3f09570761ee3ab3e987ffa0d9a37d379d23c8c78d9fc924',
    'src/main/java/dev/futurae/veilbound/client/screen/VeilInventoryScreen.java': '11d82430c13c0a15b21f08c6f39c1e4b2209904da72040c0cf6bd43177352ab3',
    'src/main/java/dev/futurae/veilbound/platform/neoforge/network/NeoForgeNetworking.java': '758df1e7fce08ff8953a658218f395fca047153df04e5208f6585fda4efa2399',
    'src/main/resources/assets/veilbound/lang/en_us.json': 'e311008de39102433503738dc1b00a50f6dc2fc84101f1707799e7cdc2f38454',
    'src/test/java/dev/futurae/veilbound/inventory/VeilInventorySelfTest.java': '8b7ee0d7c391f7ac004c1cc8ad26e2616f189d96e80a77d52aee0f9e147a21ea',
    'src/test/java/dev/futurae/veilbound/inventory/VeilCraftingSelfTest.java': 'c8cc7473ccfda62bf8474b3975eed8d48da5adb32a4a7ac7f779fca83322e17c',
    'src/test/java/dev/futurae/veilbound/inventory/VeilTransmutationSelfTest.java': '48bb83b24447748f24b7d7e6c3a1b2779aa807eeb28e30400111100a5979a6aa',
}
for rel, want in expected.items():
    got = hashlib.sha256((root / rel).read_bytes()).hexdigest()
    if got != want:
        raise SystemExit(f'{rel}: checksum mismatch {got} != {want}')
print('VEILBOUND_0165_APPLY=PASS files=%d' % len(expected))
