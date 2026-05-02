#!/usr/bin/env bash
set -euo pipefail

ROOT="$(unset CDPATH; cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_HOME_DIR="${CLAUDE_HOME:-$HOME/.claude}"
TOKEN_TRANS_SKILL_DIR="${TOKTRANS_CLAUDE_SKILL_DIR:-$CLAUDE_HOME_DIR/skills/token-trans}"
SOURCE_SKILL_DIR="$ROOT/skills/claude-code/token-trans"

usage() {
  cat <<'USAGE'
Usage: scripts/install-claude-code.sh [--home PATH]

Installs the TokTrans Claude Code skill ($token-trans) into Claude Code's
user-level skills directory. Does not modify the official `claude` CLI.

Options:
  --home PATH   Install under PATH instead of ~/.claude.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --home) shift; CLAUDE_HOME_DIR="$1"; TOKEN_TRANS_SKILL_DIR="$CLAUDE_HOME_DIR/skills/token-trans" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [ ! -f "$SOURCE_SKILL_DIR/SKILL.md" ]; then
  echo "Source skill not found: $SOURCE_SKILL_DIR/SKILL.md" >&2
  exit 1
fi

if [ -f "$TOKEN_TRANS_SKILL_DIR/SKILL.md" ] && ! grep -Fq 'name: token-trans' "$TOKEN_TRANS_SKILL_DIR/SKILL.md"; then
  echo "Refusing to overwrite non-token-trans skill: $TOKEN_TRANS_SKILL_DIR" >&2
  exit 1
fi

mkdir -p "$TOKEN_TRANS_SKILL_DIR"
cp "$SOURCE_SKILL_DIR/SKILL.md" "$TOKEN_TRANS_SKILL_DIR/SKILL.md"

cat <<EOF
TokTrans Claude Code skill installed.

Skill:
  $TOKEN_TRANS_SKILL_DIR/SKILL.md
  Invoke with: \$token-trans <your non-English task>

Verify:
  test -f "$TOKEN_TRANS_SKILL_DIR/SKILL.md" && echo "ok"

Uninstall:
  rm -rf "$TOKEN_TRANS_SKILL_DIR"
EOF
