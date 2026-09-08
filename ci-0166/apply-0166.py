from pathlib import Path
import base64, hashlib, json, shutil, sys, tarfile

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
    'src/main/resources/data/minecraft/tags/blocks',
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

# Replace starter-shell regression assumptions from the old 1x1x2 prototype with the actual
# centered 3x3x3 first-release geometry. Keep this as a real collision regression, not a disabled test.
boundary_test = root / 'src/test/java/dev/futurae/veilbound/network/VeilBoundarySnapshotPayloadSelfTest.java'
shutil.copyfile(ci / 'VeilBoundarySnapshotPayloadSelfTest.java', boundary_test)
owner_travel_test = root / 'src/test/java/dev/futurae/veilbound/domain/OwnerDomainTravelSelfTest.java'
owner_text = owner_travel_test.read_text(encoding='utf-8')
owner_text = owner_text.replace('initial pocket stays 1x1x2', 'initial Domain stays centered 3x3x3')
owner_travel_test.write_text(owner_text, encoding='utf-8')

# Keep the Core-control regression aligned with the actual first-release balance contract:
# TransductionPolicy is (FE per Matter, Matter per DE), so 96 FE + 32 Matter must credit 1 DE.
core_control_test = root / 'src/test/java/dev/futurae/veilbound/domain/CoreControlSelfTest.java'
shutil.copyfile(ci / 'CoreControlSelfTest.java', core_control_test)

# Pre-test hardening: the actively registered /domain admin surface must exercise only the slim
# first-release state model. In particular, admin-created Domains must initialize exactly like a
# Genesis Seed instead of creating the old core-inactive prototype state.
admin = root / 'src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeDomainAdminCommandCoordinator.java'
shutil.copyfile(ci / 'NeoForgeDomainAdminCommandCoordinator.java', admin)

# The Dynamo is a visible first-release machine. Give its vanilla container title a real translation
# and remove the stale Spatial Generator wording from the active block source.
lang_path = root / 'src/main/resources/assets/veilbound/lang/en_us.json'
lang = json.loads(lang_path.read_text(encoding='utf-8'))
lang['container.veilbound.boundary_dynamo'] = 'Boundary Dynamo'
lang_path.write_text(json.dumps(lang, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

dynamo = root / 'src/main/java/dev/futurae/veilbound/block/BoundaryDynamoBlock.java'
dynamo_text = dynamo.read_text(encoding='utf-8')
dynamo_text = dynamo_text.replace(
    'Pre-Core FE source used to bootstrap the Spatial Generator without requiring another tech mod.\n * The machine uses ordinary furnace fuels to drive a boundary-induction coil.',
    'Early first-release FE source for the Dimensional Transducer without requiring another tech mod.\n * The machine uses ordinary furnace fuels to drive a boundary-induction coil.')
dynamo.write_text(dynamo_text, encoding='utf-8')

# Turn the existing loader-neutral first-release regression mains into real `check` gates. These
# cover binding/starter geometry, Core controls, all four Transducer throughputs, Matter intake,
# the hybrid terminal, terminal paging/search, and atomic crafting before a human client test.
build_file = root / 'build.gradle'
build_text = build_file.read_text(encoding='utf-8')
marker = "// VEILBOUND_0166_FIRST_RELEASE_SELF_TESTS"
if marker not in build_text:
    build_text += '''

// VEILBOUND_0166_FIRST_RELEASE_SELF_TESTS
def firstReleaseSelfTests = [
    genesisSeedSelfTest: 'dev.futurae.veilbound.ritual.GenesisSeedSelfTest',
    starterPocketLayoutSelfTest: 'dev.futurae.veilbound.domain.StarterPocketLayoutSelfTest',
    coreControlSelfTest: 'dev.futurae.veilbound.domain.CoreControlSelfTest',
    transducerTierSelfTest: 'dev.futurae.veilbound.energy.TransducerTierSelfTest',
    dimensionalTransducerSelfTest: 'dev.futurae.veilbound.energy.DimensionalTransducerSelfTest',
    transducerMatterInputSelfTest: 'dev.futurae.veilbound.energy.TransducerMatterInputSelfTest',
    veilInventorySelfTest: 'dev.futurae.veilbound.inventory.VeilInventorySelfTest',
    veilInventoryTerminalPageSelfTest: 'dev.futurae.veilbound.inventory.VeilInventoryTerminalPageSelfTest',
    veilCraftingSelfTest: 'dev.futurae.veilbound.inventory.VeilCraftingSelfTest'
]
firstReleaseSelfTests.each { taskName, testMain ->
    tasks.register(taskName, JavaExec) {
        dependsOn testClasses
        classpath = sourceSets.test.runtimeClasspath
        mainClass = testMain
    }
    check.dependsOn tasks.named(taskName)
}
'''
    build_file.write_text(build_text, encoding='utf-8')

print(f'VEILBOUND_0166_APPLY=PASS chunks={len(chunks)} sha256={actual} packet_type=restored pylon_coordinator=removed starter_test=3x3x3 core_balance_test=96fe+32matter admin_surface=slim stale_tags=removed dynamo_title=translated')
