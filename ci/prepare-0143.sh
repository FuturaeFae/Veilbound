#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-Veilbound-0.1.37-dev-source}"

if [ ! -d "$ROOT" ]; then
  echo "Missing extracted source root: $ROOT" >&2
  exit 1
fi

# 0.1.38 physical boundary + shader foundation
echo "84fda69771fffcd07570962461c79eeddd4265980ef93bb6f00ff40291f829cb  ci/0138-overlay.tar.gz" | sha256sum -c -
rm -rf /tmp/vb138
mkdir -p /tmp/vb138
tar -xzf ci/0138-overlay.tar.gz -C /tmp/vb138
patch -p1 -d "$ROOT" < /tmp/vb138/ci/0138-existing.patch
cp -R /tmp/vb138/ci/overlays/0138/src/. "$ROOT/src/"
python3 ci/0138-render-compat.py "$ROOT"
python3 ci/0138-collision-compat.py "$ROOT"

# Minecraft / NeoForge 26.2 baseline migration
python3 ci/apply-26.2-compat.py "$ROOT"

# 0.1.39 live boundary repair
echo "e479fb486538ed8fde15f261555bbe32298d32eb910282ad7ba37c404031a7bd  ci/0139-overlay.tar.gz" | sha256sum -c -
rm -rf /tmp/vb139
mkdir -p /tmp/vb139
tar -xzf ci/0139-overlay.tar.gz -C /tmp/vb139
cp -R /tmp/vb139/. "$ROOT/"

# 0.1.40 movement clearance
python3 ci/0140-boundary-clearance.py "$ROOT"

# 0.1.41 domain admin + seamless/volumetric shader base
python3 ci/0141-domain-admin.py "$ROOT"
python3 ci/0141-volumetric-boundary.py "$ROOT"

# 0.1.42 reversed-Z rendering fix
python3 ci/0142-reversed-depth.py "$ROOT"

# 0.1.43 permanent vanilla-cloud suppression
python3 ci/0143-no-domain-clouds.py "$ROOT"

grep -q '^mod_version=0.1.43-dev$' "$ROOT/gradle.properties"
grep -q 'new NoDomainCloudsRenderer()' "$ROOT/src/main/java/dev/futurae/veilbound/client/VeilboundClient.java"
grep -q 'return true;' "$ROOT/src/main/java/dev/futurae/veilbound/client/render/NoDomainCloudsRenderer.java"
grep -q '"neoforge:custom_clouds": "veilbound:no_clouds"' "$ROOT/src/main/resources/data/veilbound/dimension_type/domain.json"
grep -q 'CompareOp.GREATER_THAN_OR_EQUAL' "$ROOT/src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderPipeline.java"

echo 'Prepared Veilbound 0.1.43-dev source successfully'
