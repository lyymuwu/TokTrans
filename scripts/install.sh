#!/usr/bin/env bash
set -euo pipefail

ROOT="$(unset CDPATH; cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_HOME="${CODEX_TOKEN_SAVER_HOME:-$HOME/.codex-token-saver}"
BIN_DIR="${CODEX_TOKEN_SAVER_BIN_DIR:-$HOME/.local/bin}"
SHIM="$BIN_DIR/codex-ts"
MANIFEST="$PLUGIN_HOME/install-manifest.json"
INSTALL_ALIAS=0
INSTALL_PATH=1
RC_FILE="${SHELL_RC_FILE:-$HOME/.zshrc}"

usage() {
  cat <<'USAGE'
Usage: scripts/install.sh [--alias] [--no-path] [--home PATH] [--bin-dir PATH]

Installs Codex Token Saver without modifying the official Codex CLI.

Options:
  --alias        Add a clearly marked alias block to the shell rc file.
  --no-path      Do not add the codex-ts bin directory to the shell rc file.
  --home PATH    Install managed files under PATH instead of ~/.codex-token-saver.
  --bin-dir PATH Create the codex-ts shim in PATH instead of ~/.local/bin.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --alias) INSTALL_ALIAS=1 ;;
    --no-path) INSTALL_PATH=0 ;;
    --home) shift; PLUGIN_HOME="$1"; MANIFEST="$PLUGIN_HOME/install-manifest.json" ;;
    --bin-dir) shift; BIN_DIR="$1"; SHIM="$BIN_DIR/codex-ts" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

mkdir -p "$PLUGIN_HOME" "$BIN_DIR"

if [ -e "$SHIM" ] && [ ! -L "$SHIM" ]; then
  echo "Refusing to overwrite unmanaged file: $SHIM" >&2
  exit 1
fi

if [ -L "$SHIM" ]; then
  target="$(readlink "$SHIM")"
  case "$target" in
    "$PLUGIN_HOME/scripts/codex-ts"|"$ROOT/scripts/codex-ts") ;;
    *) echo "Refusing to replace symlink not managed by this plugin: $SHIM -> $target" >&2; exit 1 ;;
  esac
fi

mkdir -p "$PLUGIN_HOME/scripts" "$PLUGIN_HOME/skills/token-saver" "$PLUGIN_HOME/.codex-plugin"
cp "$ROOT/scripts/codex-ts" "$PLUGIN_HOME/scripts/codex-ts"
cp "$ROOT/scripts/token_saver.py" "$PLUGIN_HOME/scripts/token_saver.py"
cp "$ROOT/scripts/doctor.sh" "$PLUGIN_HOME/scripts/doctor.sh"
cp "$ROOT/scripts/uninstall.sh" "$PLUGIN_HOME/scripts/uninstall.sh"
cp "$ROOT/config.example.toml" "$PLUGIN_HOME/config.example.toml"
cp "$ROOT/.codex-plugin/plugin.json" "$PLUGIN_HOME/.codex-plugin/plugin.json"
cp "$ROOT/skills/token-saver/SKILL.md" "$PLUGIN_HOME/skills/token-saver/SKILL.md"
chmod +x "$PLUGIN_HOME/scripts/codex-ts" "$PLUGIN_HOME/scripts/token_saver.py" "$PLUGIN_HOME/scripts/doctor.sh" "$PLUGIN_HOME/scripts/uninstall.sh"

if [ ! -f "$PLUGIN_HOME/config.toml" ]; then
  cp "$ROOT/config.example.toml" "$PLUGIN_HOME/config.toml"
elif grep -Fq 'provider = "openai"' "$PLUGIN_HOME/config.toml" \
  && grep -Fq 'model = "gpt-5-nano"' "$PLUGIN_HOME/config.toml" \
  && grep -Fq 'api_key_env = "OPENAI_API_KEY"' "$PLUGIN_HOME/config.toml" \
  && ! grep -Fq 'codex_model' "$PLUGIN_HOME/config.toml"; then
  cp "$PLUGIN_HOME/config.toml" "$PLUGIN_HOME/config.toml.bak"
  cp "$ROOT/config.example.toml" "$PLUGIN_HOME/config.toml"
fi

if ! grep -Fq 'detect_latin_languages' "$PLUGIN_HOME/config.toml"; then
  {
    printf '\n# Added by Codex Token Saver upgrade: enable auto-detection for Latin-script non-English prompts.\n'
    printf 'detect_latin_languages = true\n'
  } >> "$PLUGIN_HOME/config.toml"
fi

ln -sfn "$PLUGIN_HOME/scripts/codex-ts" "$SHIM"

rc_block_written=false
if [ "$INSTALL_PATH" -eq 1 ] || [ "$INSTALL_ALIAS" -eq 1 ]; then
  begin="# >>> codex-token-saver managed block >>>"
  end="# <<< codex-token-saver managed block <<<"
  touch "$RC_FILE"
  if grep -Fq "$begin" "$RC_FILE"; then
    rc_block_written=true
  else
    {
      printf '\n%s\n' "$begin"
      if [ "$INSTALL_PATH" -eq 1 ]; then
        # shellcheck disable=SC2016
        printf 'export PATH=%q:"$PATH"\n' "$BIN_DIR"
      fi
      if [ "$INSTALL_ALIAS" -eq 1 ]; then
        printf 'alias codex=%q\n' "$SHIM"
      fi
      printf '%s\n' "$end"
    } >> "$RC_FILE"
    rc_block_written=true
  fi
fi

python3 - "$MANIFEST" "$PLUGIN_HOME" "$SHIM" "$RC_FILE" "$rc_block_written" <<'PY'
import json, sys, time
manifest, home, shim, rc_file, rc_written = sys.argv[1:]
data = {
    "tool": "codex-token-saver",
    "version": "0.1.0",
    "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "plugin_home": home,
    "managed_paths": [
        f"{home}/scripts/codex-ts",
        f"{home}/scripts/token_saver.py",
        f"{home}/scripts/doctor.sh",
        f"{home}/scripts/uninstall.sh",
        f"{home}/config.example.toml",
        f"{home}/.codex-plugin/plugin.json",
        f"{home}/skills/token-saver/SKILL.md",
        shim,
    ],
    "user_preserved_paths": [
        f"{home}/config.toml",
        f"{home}/logs",
    ],
    "shell_rc_file": rc_file if rc_written == "true" else None,
    "managed_rc_block": rc_written == "true",
}
with open(manifest, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY

cat <<EOF
Codex Token Saver installed.

Command:
  $SHIM

Shell PATH:
  Added a managed block to $RC_FILE so new shells can run codex-ts directly.
  For this already-open shell, run: source "$RC_FILE"

Optional alias, if you want codex to mean codex-ts:
  alias codex='$SHIM'

Config:
  $PLUGIN_HOME/config.toml

Run:
  codex-ts doctor
EOF
