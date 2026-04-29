#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(unset CDPATH; cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
status=0
if [ -f "$SCRIPT_DIR/token_saver.py" ]; then
  "${PYTHON:-python3}" "$SCRIPT_DIR/token_saver.py" doctor || status=$?
else
  echo "Wrapper: not installed (skill-only install)"
fi

TOKEN_TRANS_SKILL_DIR="${CODEX_TOKEN_TRANS_SKILL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills/token-trans}"
if [ -f "$TOKEN_TRANS_SKILL_DIR/SKILL.md" ] && grep -Fq 'name: token-trans' "$TOKEN_TRANS_SKILL_DIR/SKILL.md"; then
  echo "Token Trans skill: installed at $TOKEN_TRANS_SKILL_DIR"
else
  echo "Token Trans skill: not installed at $TOKEN_TRANS_SKILL_DIR"
fi

exit "$status"
