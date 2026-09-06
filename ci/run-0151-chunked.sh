#!/usr/bin/env bash
set -euo pipefail
cp ci/build-0151.sh /tmp/build-0151.sh
sed -i 's#base64 --decode ci-0151/runtime.b64 > runtime-0151.tar.xz#cat ci-0151/runtime-part-*.b64 | base64 --decode > runtime-0151.tar.xz#' /tmp/build-0151.sh
bash /tmp/build-0151.sh
