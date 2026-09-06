#!/usr/bin/env bash
set -euo pipefail

ROOT=Veilbound-0.1.37-dev-source
BASELINE_COMMIT=6a8362d6e40978caa6997b2346303ffa5965b307

git fetch --no-tags --depth=1 origin "$BASELINE_COMMIT"
git show "$BASELINE_COMMIT:Veilbound-0.1.37-dev-source.zip" > Veilbound-0.1.37-dev-source.zip
git show "$BASELINE_COMMIT:ci/apply-26.2-compat.py" > apply-26.2-compat.py
echo "e36b2721698d091b4a375b553b22be1f80ad22cc8b0242e40f399ea0ad81eab3  Veilbound-0.1.37-dev-source.zip" | sha256sum -c -
unzip -q Veilbound-0.1.37-dev-source.zip
python3 apply-26.2-compat.py "$ROOT"

cat ci-0148/part-*.b64 | base64 --decode > overlay-0148.tar.xz
echo "f314493cd063871026ce4d0907a8f582d43f09942db355065f551acd8199e710  overlay-0148.tar.xz" | sha256sum -c -
tar -xJf overlay-0148.tar.xz -C "$ROOT"
base64 --decode ci-0148/resources.b64 > resources-0148.tar.xz
echo "80efff69a0e8ee9016079940af4647dfb9b1892eed7933e2ba627000c58449a5  resources-0148.tar.xz" | sha256sum -c -
tar -xJf resources-0148.tar.xz -C "$ROOT/src/main/resources"
base64 --decode ci-0149/patch.b64 > patch-0149.xz
echo "dad558517d14a350bcc57b7430ac04c24cd63a955826f9b74b307bafa262806d  patch-0149.xz" | sha256sum -c -
xz -dc patch-0149.xz | patch -d "$ROOT" -p1
cat ci-0149/binpart-*.b64 | base64 --decode > binary-0149.tar.xz
echo "fe07254ef175ca8c15fd1c8a9e7588589362566c10d72b7c90fee61f90832c3a  binary-0149.tar.xz" | sha256sum -c -
tar -xJf binary-0149.tar.xz -C "$ROOT/src/main/resources"
base64 --decode ci-0149/fogfix.b64 > fogfix-0149.xz
echo "a66f4aec0b9d37cd2f8df1889ecfc97a764f638eca00d2e563796bfd5e59ee2f  fogfix-0149.xz" | sha256sum -c -
xz -dc fogfix-0149.xz | patch -d "$ROOT" -p1

cat ci-0150/patchpart-*.b64 | base64 --decode > patch-0150.xz
echo "d56e1ffac10bf7440c48aa5c6850f61b54d2b3578ba0fbf9b6a8b273c2ad07e9  patch-0150.xz" | sha256sum -c -
xz -dc patch-0150.xz > patch-0150.diff
set +e
patch -d "$ROOT" -p1 < patch-0150.diff
PATCH_RC=$?
set -e
test "$PATCH_RC" -eq 1
test -f "$ROOT/README.md.rej"
test -f "$ROOT/src/main/resources/assets/veilbound/lang/en_us.json.rej"
test "$(find "$ROOT" -name '*.rej' -type f | wc -l)" -eq 2
find "$ROOT" \( -name '*.rej' -o -name '*.orig' \) -type f -delete
cat ci-0150/binpart-*.b64 | base64 --decode > binary-0150.tar.xz
echo "dbb4b9974a3cdcf20fd798ea94daa098d547fa2e2de97fd8ce5a6eea5461034d  binary-0150.tar.xz" | sha256sum -c -
tar -xJf binary-0150.tar.xz -C "$ROOT"
cat ci-0150/runtimechunk-*.b64 | base64 --decode > runtime-0150.tar.xz
echo "41dfa3374992a0607f57d71a1d57747736b55fcf1521044fbf822eb8b43e24ee  runtime-0150.tar.xz" | sha256sum -c -
tar -xJf runtime-0150.tar.xz -C "$ROOT"
base64 --decode ci-0150/compilefix.b64 > compilefix-0150.xz
echo "ede3ee2caad83fa62884ee1bbe67e2fcadb39a116c7a3f1e22db591517513e4e  compilefix-0150.xz" | sha256sum -c -
xz -dc compilefix-0150.xz | patch -d "$ROOT" -p1

python3 - <<'PY'
import json
from pathlib import Path
p=Path('Veilbound-0.1.37-dev-source/src/main/resources/assets/veilbound/lang/en_us.json')
d=json.loads(p.read_text(encoding='utf-8'))
d.update({
'block.veilbound.chronal_engine_block':'Chronal Engine Block','block.veilbound.mnemonic_nexus_block':'Mnemonic Nexus Block','block.veilbound.axiom_crucible_block':'Axiom Crucible Block','block.veilbound.horizon_stabilizer_block':'Horizon Stabilizer Block','item.veilbound.chronal_rotor':'Chronal Rotor','item.veilbound.continuity_stator':'Continuity Stator','item.veilbound.causal_governor':'Causal Governor','item.veilbound.worldline_gimbal':'Worldline Gimbal','item.veilbound.mnemonic_focal_core':'Mnemonic Focal Core','item.veilbound.recollection_bus':'Recollection Bus','item.veilbound.law_manifold':'Law Manifold','item.veilbound.axiom_seal':'Axiom Seal','item.veilbound.paradox_dampener':'Paradox Dampener','item.veilbound.horizon_frame':'Horizon Frame','item.veilbound.singularity_baffle':'Singularity Baffle','item.veilbound.ontology_injector':'Ontology Injector','item.veilbound.reality_synchronizer':'Reality Synchronizer','item.veilbound.transfinite_arbiter':'Transfinite Arbiter','item.veilbound.worldline_heart':'Worldline Heart','item.veilbound.sovereign_lattice_core':'Sovereign Lattice Core','item.veilbound.event_horizon_key':'Event Horizon Key','item.veilbound.causality_crown':'Causality Crown','item.veilbound.mnemonic_constellation':'Mnemonic Constellation','item.veilbound.axiomatic_invariant':'Axiomatic Invariant'})
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
PY

base64 --decode ci-0151/runtime.b64 > runtime-0151.xz
echo "331960083ac8d99e755e90a302439cd9bc5d9794392cbaddd8c7aed2608ebaaf  runtime-0151.xz" | sha256sum -c -
xz -dc runtime-0151.xz | patch -d "$ROOT" -p1

python3 - <<'PY'
import json
from pathlib import Path
p=Path('Veilbound-0.1.37-dev-source/src/main/resources/assets/veilbound/lang/en_us.json')
d=json.loads(p.read_text(encoding='utf-8'))
d.update({
'message.veilbound.monument.enabled':'%s field enabled','message.veilbound.monument.disabled':'%s field disabled','message.veilbound.monument.status':'%s — enabled: %s, status: %s, maintenance: %s DE/s, Core DE: %s','codex.veilbound.monuments.title':'Ascendant Monuments','codex.veilbound.monuments.1':'The four Ascendant monuments are one-block anchors with oversized animated geometry and fitted physical collision.','codex.veilbound.monuments.2':'They bind to the placing owner and project only inside that owner’s live Domain with an active Ascendant-or-higher Core.','codex.veilbound.monuments.3':'Chronal Engine: 2,048 DE/s; doubles only Dimensional Fabricator and Veil Foundry process cadence.','codex.veilbound.monuments.4':'Mnemonic Nexus: 1,536 DE/s; doubles concrete Veilbound Memory pulse intensity such as Verdant Fertility attempts.','codex.veilbound.monuments.5':'Axiom Crucible: 3,072 DE/s; other monument fields pay only 75% maintenance while its field is live.','codex.veilbound.monuments.6':'Horizon Stabilizer: 4,096 DE/s; repairs 1 fracture each second but does not seal an already-open Breach.','codex.veilbound.monuments.7':'Empty-hand use reports status. Sneak + empty hand toggles the field.','codex.veilbound.monuments.8':'Fields suspend on insufficient DE and vanish automatically when unloaded, invalid, disabled, or restarted.','codex.veilbound.monuments.9':'Animated energy rings remain non-solid; bases, towers, cores, crowns and outriggers use fitted oversized collision.'})
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
PY

grep -q '^mod_version=0.1.51-dev$' "$ROOT/gradle.properties"
KIND="$ROOT/src/main/java/dev/futurae/veilbound/engineering/EngineeringMonumentKind.java"
FIELDS="$ROOT/src/main/java/dev/futurae/veilbound/engineering/EngineeringMonumentFieldTracker.java"
BE="$ROOT/src/main/java/dev/futurae/veilbound/block/entity/EngineeringMonumentBlockEntity.java"
BLOCK="$ROOT/src/main/java/dev/futurae/veilbound/block/EngineeringMonumentBlock.java"
STATION="$ROOT/src/main/java/dev/futurae/veilbound/block/entity/EngineeringStationBlockEntity.java"
MEMORY="$ROOT/src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeMemoryEffectCoordinator.java"
INTERACT="$ROOT/src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeEngineeringStationController.java"
CODEX="$ROOT/src/main/java/dev/futurae/veilbound/client/screen/EngineeringCodexScreen.java"
TEST="$ROOT/src/test/java/dev/futurae/veilbound/engineering/EngineeringMonumentFieldTrackerSelfTest.java"
test -f "$KIND" && test -f "$FIELDS" && test -f "$TEST"
grep -q 'CHRONAL(2_048L)' "$KIND"; grep -q 'MNEMONIC(1_536L)' "$KIND"; grep -q 'AXIOM(3_072L)' "$KIND"; grep -q 'HORIZON(4_096L)' "$KIND"
grep -q 'AXIOM_NETWORK_MAINTENANCE_MULTIPLIER = 0.75D' "$FIELDS"
grep -q 'CHRONAL_ENGINEERING_PROGRESS_MULTIPLIER = 2' "$FIELDS"
grep -q 'MNEMONIC_MEMORY_PULSE_MULTIPLIER = 2' "$FIELDS"
grep -q 'HORIZON_FRACTURE_REPAIR_PER_SECOND = 1.0D' "$FIELDS"
grep -q 'DEFAULT_MAXIMUM_AGE_TICKS = 40' "$FIELDS"
grep -q 'withdraw(ownerId, sourceKey' "$BE"; grep -q 'HORIZON_FRACTURE_REPAIR_PER_SECOND' "$BE"
grep -q 'setPlacedBy' "$BLOCK"; grep -q 'getTicker' "$BLOCK"; grep -q 'monumentBox(0.36, 2.61, 0.36, 0.64, 3.08, 0.64)' "$BLOCK"
grep -q 'CHRONAL_ENGINEERING_PROGRESS_MULTIPLIER' "$STATION"
grep -q 'MNEMONIC_MEMORY_PULSE_MULTIPLIER' "$MEMORY"
grep -q 'message.veilbound.monument.status' "$INTERACT"
grep -q '"monuments"' "$CODEX"
grep -q 'engineeringMonumentFieldSelfTest' "$ROOT/build.gradle"
for ore in resonant phase mnemonic_crystal causalite axiomite paradox; do test -f "$ROOT/src/main/resources/assets/veilbound/blockstates/${ore}_ore.json"; test -f "$ROOT/src/main/resources/assets/veilbound/blockstates/deepslate_${ore}_ore.json"; done
VSH="$ROOT/src/main/resources/assets/veilbound/shaders/core/veil_boundary_fog.vsh"; FSH="$ROOT/src/main/resources/assets/veilbound/shaders/core/veil_boundary_fog.fsh"
grep -q 'fogFieldPos = UV0;' "$VSH"; grep -q 'in vec2 fogFieldPos;' "$FSH"; ! grep -q 'fogWorldPos' "$VSH" "$FSH"
test -f "$ROOT/src/main/resources/assets/veilbound/shaders/core/engineering_monument.vsh"; test -f "$ROOT/src/main/resources/assets/veilbound/shaders/core/engineering_monument.fsh"
python3 - <<'PY'
import json
from pathlib import Path
root=Path('Veilbound-0.1.37-dev-source/src/main/resources')
def strict_pairs(pairs):
 out={}
 for k,v in pairs:
  if k in out: raise ValueError(f'duplicate JSON key {k}')
  out[k]=v
 return out
files=list(root.rglob('*.json'))+list(root.rglob('*.png.mcmeta'))
for p in files: json.loads(p.read_text(encoding='utf-8'),object_pairs_hook=strict_pairs)
recipes=list((root/'data/veilbound/veilbound/engineering_recipes').glob('*.json')); assert len(recipes)==120
assert len(list(root.rglob('*.png.mcmeta')))==74
outputs=[json.loads(p.read_text(encoding='utf-8'))['output']['item'] for p in recipes]; assert len(outputs)==len(set(outputs))
lang=json.loads((root/'assets/veilbound/lang/en_us.json').read_text(encoding='utf-8')); assert 'codex.veilbound.monuments.title' in lang
print(f'VEILBOUND_0151_RESOURCE_AUDIT=PASS recipes={len(recipes)} json_like={len(files)} animations=74')
PY

(cd "$ROOT" && gradle --no-daemon --stacktrace build)
JAR="$(find "$ROOT/build/libs" -maxdepth 1 -type f -name '*.jar' ! -name '*sources*' ! -name '*javadoc*' -print -quit)"
test -n "$JAR"; cp "$JAR" Veilbound-0.1.51-dev.jar
unzip -t Veilbound-0.1.51-dev.jar
unzip -p Veilbound-0.1.51-dev.jar META-INF/neoforge.mods.toml | grep -q 'version="0.1.51-dev"'
unzip -p Veilbound-0.1.51-dev.jar assets/veilbound/lang/en_us.json | grep -q 'codex.veilbound.monuments.title'
unzip -p Veilbound-0.1.51-dev.jar assets/veilbound/shaders/core/veil_boundary_fog.vsh | grep -q 'fogFieldPos = UV0;'
! unzip -p Veilbound-0.1.51-dev.jar assets/veilbound/shaders/core/veil_boundary_fog.vsh | grep -q 'fogWorldPos'
for cls in EngineeringMonumentBlock EngineeringMonumentCollisionState EngineeringMonumentBlockEntity EngineeringMonumentRenderer EngineeringMonumentRenderPipelines EngineeringMonumentFieldTracker EngineeringMonumentKind; do unzip -l Veilbound-0.1.51-dev.jar | grep -q "$cls.class"; done
unzip -l Veilbound-0.1.51-dev.jar | grep -q 'assets/veilbound/shaders/core/engineering_monument.vsh'; unzip -l Veilbound-0.1.51-dev.jar | grep -q 'assets/veilbound/shaders/core/engineering_monument.fsh'
python3 - <<'PY'
import zipfile
with zipfile.ZipFile('Veilbound-0.1.51-dev.jar') as zf:
 recipes=[n for n in zf.namelist() if n.startswith('data/veilbound/veilbound/engineering_recipes/') and n.endswith('.json')]; assert len(recipes)==120
print('VEILBOUND_PACKAGED_RECIPE_COUNT=120')
PY
sha256sum Veilbound-0.1.51-dev.jar > Veilbound-0.1.51-dev-SHA256SUMS.txt

mkdir -p smoke-server; cd smoke-server
curl --fail --location --retry 3 --output neoforge-installer.jar https://maven.neoforged.net/releases/net/neoforged/neoforge/26.2.0.75/neoforge-26.2.0.75-installer.jar
java -jar neoforge-installer.jar --installServer
mkdir -p mods; cp ../Veilbound-0.1.51-dev.jar mods/
printf 'eula=true\n' > eula.txt; printf 'online-mode=false\n' > server.properties; chmod +x run.sh
set +e; timeout 120s ./run.sh nogui > ../Veilbound-0.1.51-dev-server-smoke.log 2>&1; RC=$?; set -e
if [ -f logs/latest.log ] && grep -Eq 'Done \(|For help, type' logs/latest.log; then echo 'VEILBOUND_SERVER_SMOKE=PASS'; else cat ../Veilbound-0.1.51-dev-server-smoke.log; echo "VEILBOUND_SERVER_SMOKE=FAIL rc=${RC}" >&2; exit 1; fi
cd ..
