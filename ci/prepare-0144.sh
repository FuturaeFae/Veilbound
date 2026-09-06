#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-Veilbound-0.1.37-dev-source}"

if [ ! -d "$ROOT" ]; then
  echo "Missing extracted source root: $ROOT" >&2
  exit 1
fi

# Rebuild the proven audited source chain through 0.1.43 first.
bash ci/prepare-0143.sh "$ROOT"

# 0.1.44 final boundary art direction: opaque black wall + true spatial fog slices + edge overlap.
python3 ci/0144-black-boundary-fog.py "$ROOT"

grep -q '^mod_version=0.1.44-dev$' "$ROOT/gradle.properties"
grep -q 'EDGE_OVERLAP = 0.10D' "$ROOT/src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderer.java"
grep -q 'FOG_LAYERS = 20' "$ROOT/src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderer.java"
grep -q 'FOG_DEPTH = 3.00D' "$ROOT/src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderer.java"
grep -q 'VeilBoundaryFogRenderPipeline::register' "$ROOT/src/main/java/dev/futurae/veilbound/client/VeilboundClient.java"
grep -q 'fragColor = vec4(0.0, 0.0, 0.0, 1.0);' "$ROOT/src/main/resources/assets/veilbound/shaders/core/veil_boundary.fsh"
test -f "$ROOT/src/main/resources/assets/veilbound/shaders/core/veil_boundary_fog.vsh"
test -f "$ROOT/src/main/resources/assets/veilbound/shaders/core/veil_boundary_fog.fsh"
grep -q '"neoforge:custom_clouds": "veilbound:no_clouds"' "$ROOT/src/main/resources/data/veilbound/dimension_type/domain.json"

echo 'Prepared Veilbound 0.1.44-dev source successfully'