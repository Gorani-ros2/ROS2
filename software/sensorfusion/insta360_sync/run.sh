#!/bin/bash
# Insta360 제어 바이너리 실행 래퍼. 바이너리는 레포 최상위의 build/ 에 빌드되어 있다(빌드 산출물은 git 제외).
ROOT=$(git -C "$(dirname "$(readlink -f "$0")")" rev-parse --show-toplevel)
exec "$ROOT/build/insta360_control" "$@"
