#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${SCRIPT_DIR}/ardupilot"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

DEFAULT_GDRIVE_FILE_ID="1dP5RG2YxI_55IvSexihVxudFBNm36l1n"
ARCHIVE_URL=""
LOCAL_ARCHIVE=""

usage() {
  cat <<USAGE
Usage:
  bash fetch_open_source_fc.sh [--archive-url URL] [--archive FILE]

Options:
  --archive-url URL  Download and import ArduPilot archive from URL first.
  --archive FILE     Import from a local archive (.zip/.tar.gz/.tgz/.tar).
  -h, --help         Show help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive-url)
      ARCHIVE_URL="${2:-}"
      shift 2
      ;;
    --archive)
      LOCAL_ARCHIVE="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[error] unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -d "${TARGET_DIR}/.git" ]]; then
  echo "[info] ardupilot already exists at ${TARGET_DIR}"
  exit 0
fi

extract_archive() {
  local archive="$1"
  local extract_dir="${TMP_DIR}/extract"
  mkdir -p "${extract_dir}"

  case "${archive}" in
    *.zip)
      unzip -q "${archive}" -d "${extract_dir}"
      ;;
    *.tar.gz|*.tgz)
      tar -xzf "${archive}" -C "${extract_dir}"
      ;;
    *.tar)
      tar -xf "${archive}" -C "${extract_dir}"
      ;;
    *)
      echo "[error] unsupported archive type: ${archive}"
      return 1
      ;;
  esac

  local root_dir
  root_dir="$(find "${extract_dir}" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
  if [[ -z "${root_dir}" ]]; then
    echo "[error] archive extraction produced no directory"
    return 1
  fi

  if [[ ! -f "${root_dir}/README.md" && ! -d "${root_dir}/libraries" ]]; then
    echo "[warn] archive content does not look like ArduPilot root: ${root_dir}"
  fi

  mv "${root_dir}" "${TARGET_DIR}"
  echo "[ok] imported archive into ${TARGET_DIR}"
}

download_archive() {
  local url="$1"
  local out_file="${TMP_DIR}/ardupilot_archive"

  if [[ "${url}" == *"drive.google.com"* && "${url}" == *"/file/d/"* ]]; then
    local file_id
    file_id="$(printf '%s' "${url}" | sed -n 's#.*\/file\/d\/\([^\/]*\)\/.*#\1#p')"
    if [[ -n "${file_id}" ]]; then
      url="https://drive.google.com/uc?export=download&id=${file_id}"
    fi
  fi

  echo "[info] downloading archive: ${url}"
  curl -fL "${url}" -o "${out_file}" || return 1

  local content_type
  content_type="$(file -b --mime-type "${out_file}")"
  case "${content_type}" in
    application/zip)
      mv "${out_file}" "${out_file}.zip"
      printf '%s\n' "${out_file}.zip"
      ;;
    application/gzip|application/x-gzip)
      mv "${out_file}" "${out_file}.tar.gz"
      printf '%s\n' "${out_file}.tar.gz"
      ;;
    application/x-tar)
      mv "${out_file}" "${out_file}.tar"
      printf '%s\n' "${out_file}.tar"
      ;;
    *)
      echo "[error] downloaded file is not a supported archive (mime: ${content_type})"
      return 1
      ;;
  esac
}

if [[ -n "${LOCAL_ARCHIVE}" ]]; then
  echo "[info] importing local archive: ${LOCAL_ARCHIVE}"
  extract_archive "${LOCAL_ARCHIVE}" && exit 0
  echo "[warn] local archive import failed, continue with network sources"
fi

if [[ -z "${ARCHIVE_URL}" ]]; then
  ARCHIVE_URL="https://drive.google.com/file/d/${DEFAULT_GDRIVE_FILE_ID}/view?usp=drive_link"
fi

if archive_path="$(download_archive "${ARCHIVE_URL}")"; then
  if extract_archive "${archive_path}"; then
    exit 0
  fi
  echo "[warn] archive download succeeded but extraction failed, fallback to git clone"
else
  echo "[warn] archive download failed, fallback to git clone"
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

echo "[error] unable to fetch ArduPilot via archive and all configured remotes"
exit 1
