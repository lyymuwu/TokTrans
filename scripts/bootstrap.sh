#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${CODEX_TOKEN_SAVER_REPO_URL:-https://github.com/lyymuwu/codex-token-saver.git}"
REF="${CODEX_TOKEN_SAVER_REF:-main}"

usage() {
  cat <<'USAGE'
Usage: curl -fsSL https://raw.githubusercontent.com/lyymuwu/codex-token-saver/main/scripts/bootstrap.sh | bash

Environment:
  CODEX_TOKEN_SAVER_REPO_URL  Override repository URL.
  CODEX_TOKEN_SAVER_REF       Git branch/tag/commit to install. Default: main.

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

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/codex-token-saver.XXXXXX")"
cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

echo "Downloading Codex Token Saver from $REPO_URL ($REF)"
git clone --depth 1 --branch "$REF" "$REPO_URL" "$tmpdir/codex-token-saver"

cd "$tmpdir/codex-token-saver"
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
