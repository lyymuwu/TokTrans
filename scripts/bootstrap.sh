#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${TOKTRANS_REPO_URL:-${CODEX_TOKEN_SAVER_REPO_URL:-https://github.com/lyymuwu/TokTrans.git}}"
REF="${TOKTRANS_REF:-${CODEX_TOKEN_SAVER_REF:-main}}"

usage() {
  cat <<'USAGE'
Usage: curl -fsSL https://raw.githubusercontent.com/lyymuwu/TokTrans/main/scripts/bootstrap.sh | bash

Environment:
  TOKTRANS_REPO_URL  Override repository URL.
  TOKTRANS_REF       Git branch/tag/commit to install. Default: main.

Extra arguments are passed to scripts/install.sh:
  bash bootstrap.sh --alias
  bash bootstrap.sh --no-path
USAGE
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

need git
need bash

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/toktrans.XXXXXX")"
cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

echo "Downloading TokTrans from $REPO_URL ($REF)"
git clone --depth 1 --branch "$REF" "$REPO_URL" "$tmpdir/TokTrans"

cd "$tmpdir/TokTrans"
echo "Running installer..."
bash ./scripts/install.sh "$@"

cat <<'NEXT'

Next:
  source ~/.zshrc
  codex-ts doctor
  $token-trans <your non-English task>

Security note:
  For maximum safety, clone the repository first and inspect scripts/install.sh before running it.
NEXT
