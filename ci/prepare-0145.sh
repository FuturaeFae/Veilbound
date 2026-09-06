#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-Veilbound-0.1.37-dev-source}"

if [ ! -d "$ROOT" ]; then
  echo "Missing extracted source root: $ROOT" >&2
  exit 1
fi

# Rebuild the proven audited source chain through 0.1.44 first.
bash ci/prepare-0144.sh "$ROOT"

# 0.1.45: denser 1-3 block fog, pure black wall, and one-block camera exclusion.
python3 ci/0145-dense-boundary-fog.py "$ROOT"

grep -q '^mod_version=0.1.45-dev$' "$ROOT/gradle.properties"
grep -q 'FOG_LAYERS = 32' "$ROOT/src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderer.java"
grep -q 'FOG_DEPTH = 3.00D' "$ROOT/src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderer.java"
grep -q 'CAMERA_CLEAR_RADIUS = 1.00D' "$ROOT/src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderer.java"
grep -q 'EDGE_OVERLAP = 0.10D' "$ROOT/src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderer.java"
grep -q 'fragColor = vec4(0.0, 0.0, 0.0, 1.0);' "$ROOT/src/main/resources/assets/veilbound/shaders/core/veil_boundary.fsh"
grep -q 'Neutral charcoal/ash fog only' "$ROOT/src/main/resources/assets/veilbound/shaders/core/veil_boundary_fog.fsh"
grep -q '"neoforge:custom_clouds": "veilbound:no_clouds"' "$ROOT/src/main/resources/data/veilbound/dimension_type/domain.json"

echo 'Prepared Veilbound 0.1.45-dev source successfully'