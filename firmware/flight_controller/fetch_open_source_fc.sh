#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${SCRIPT_DIR}/ardupilot"

if [[ -d "${TARGET_DIR}/.git" ]]; then
  echo "[info] ardupilot already exists at ${TARGET_DIR}"
  exit 0
fi

REPO_CANDIDATES=(
  "https://github.com/ArduPilot/ardupilot.git"
  "https://gitee.com/mirrors/ardupilot.git"
)

for repo in "${REPO_CANDIDATES[@]}"; do
  echo "[info] trying clone from ${repo}"
  if git clone --depth 1 "${repo}" "${TARGET_DIR}"; then
    echo "[ok] cloned ArduPilot into ${TARGET_DIR}"
    exit 0
  fi
  echo "[warn] clone failed from ${repo}, trying next mirror"
done

echo "[error] unable to clone ArduPilot from all configured remotes"
exit 1
