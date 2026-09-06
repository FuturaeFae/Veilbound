#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-Veilbound-0.1.37-dev-source}"

if [ ! -d "$ROOT" ]; then
  echo "Missing extracted source root: $ROOT" >&2
  exit 1
fi

# Rebuild the proven audited source chain through 0.1.46 first.
bash ci/prepare-0146.sh "$ROOT"

# 0.1.47: cheap world-space detail noise to hide slice banding/pixelation.
python3 ci/0147-fog-detail-noise.py "$ROOT"

grep -q '^mod_version=0.1.47-dev$' "$ROOT/gradle.properties"
grep -q 'FOG_LAYERS = 16' "$ROOT/src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderer.java"
grep -q 'FOG_DEPTH = 3.00D' "$ROOT/src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderer.java"
grep -q 'CAMERA_CLEAR_RADIUS = 1.00D' "$ROOT/src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderer.java"
grep -q 'EDGE_OVERLAP = 0.10D' "$ROOT/src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderer.java"
grep -q 'float detailNoise = noise3(detailCoord);' "$ROOT/src/main/resources/assets/veilbound/shaders/core/veil_boundary_fog.fsh"
grep -q 'detailStrength = mix(0.055, 0.14' "$ROOT/src/main/resources/assets/veilbound/shaders/core/veil_boundary_fog.fsh"
grep -q 'fragColor = vec4(0.0, 0.0, 0.0, 1.0);' "$ROOT/src/main/resources/assets/veilbound/shaders/core/veil_boundary.fsh"
grep -q '"neoforge:custom_clouds": "veilbound:no_clouds"' "$ROOT/src/main/resources/data/veilbound/dimension_type/domain.json"

echo 'Prepared Veilbound 0.1.47-dev source successfully'
