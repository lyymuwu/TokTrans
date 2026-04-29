#!/usr/bin/env bash
set -euo pipefail

ROOT="$(unset CDPATH; cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_HOME="${CODEX_TOKEN_SAVER_HOME:-$HOME/.codex-token-saver}"
BIN_DIR="${CODEX_TOKEN_SAVER_BIN_DIR:-$HOME/.local/bin}"
SHIM="$BIN_DIR/codex-ts"
MANIFEST="$PLUGIN_HOME/install-manifest.json"
INSTALL_ALIAS=0
INSTALL_PATH=1
INSTALL_WRAPPER=1
RC_FILE="${SHELL_RC_FILE:-$HOME/.zshrc}"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
TOKEN_TRANS_SKILL_DIR="${CODEX_TOKEN_TRANS_SKILL_DIR:-$CODEX_HOME_DIR/skills/token-trans}"
INSTALL_SKILL=1

usage() {
  cat <<'USAGE'
Usage: scripts/install.sh [--skill-only] [--alias] [--no-path] [--no-skill] [--home PATH] [--bin-dir PATH]

Installs Codex Token Saver without modifying the official Codex CLI.

Options:
  --skill-only   Install only the $token-trans Codex skill.
  --alias        Add a clearly marked alias block to the shell rc file.
  --no-path      Do not add the codex-ts bin directory to the shell rc file.
  --no-skill     Do not install the $token-trans Codex skill.
  --home PATH    Install managed files under PATH instead of ~/.codex-token-saver.
  --bin-dir PATH Create the codex-ts shim in PATH instead of ~/.local/bin.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --alias) INSTALL_ALIAS=1 ;;
    --skill-only) INSTALL_WRAPPER=0; INSTALL_SKILL=1 ;;
    --no-path) INSTALL_PATH=0 ;;
    --no-skill) INSTALL_SKILL=0 ;;
    --home) shift; PLUGIN_HOME="$1"; MANIFEST="$PLUGIN_HOME/install-manifest.json" ;;
    --bin-dir) shift; BIN_DIR="$1"; SHIM="$BIN_DIR/codex-ts" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [ "$INSTALL_WRAPPER" -eq 0 ]; then
  INSTALL_ALIAS=0
  INSTALL_PATH=0
fi

mkdir -p "$PLUGIN_HOME"

if [ "$INSTALL_WRAPPER" -eq 1 ]; then
  mkdir -p "$BIN_DIR"

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
fi

mkdir -p "$PLUGIN_HOME/scripts" "$PLUGIN_HOME/skills/token-saver" "$PLUGIN_HOME/.codex-plugin"
cp "$ROOT/scripts/doctor.sh" "$PLUGIN_HOME/scripts/doctor.sh"
cp "$ROOT/scripts/uninstall.sh" "$PLUGIN_HOME/scripts/uninstall.sh"
cp "$ROOT/.codex-plugin/plugin.json" "$PLUGIN_HOME/.codex-plugin/plugin.json"
cp "$ROOT/skills/token-saver/SKILL.md" "$PLUGIN_HOME/skills/token-saver/SKILL.md"
chmod +x "$PLUGIN_HOME/scripts/doctor.sh" "$PLUGIN_HOME/scripts/uninstall.sh"

if [ "$INSTALL_WRAPPER" -eq 1 ]; then
  cp "$ROOT/scripts/codex-ts" "$PLUGIN_HOME/scripts/codex-ts"
  cp "$ROOT/scripts/token_saver.py" "$PLUGIN_HOME/scripts/token_saver.py"
  cp "$ROOT/config.example.toml" "$PLUGIN_HOME/config.example.toml"
  chmod +x "$PLUGIN_HOME/scripts/codex-ts" "$PLUGIN_HOME/scripts/token_saver.py"
fi

if [ "$INSTALL_SKILL" -eq 1 ]; then
  if [ -f "$TOKEN_TRANS_SKILL_DIR/SKILL.md" ] && ! grep -Fq 'name: token-trans' "$TOKEN_TRANS_SKILL_DIR/SKILL.md"; then
    echo "Refusing to overwrite non-token-trans skill: $TOKEN_TRANS_SKILL_DIR" >&2
    exit 1
  fi
  mkdir -p "$TOKEN_TRANS_SKILL_DIR/agents"
  cp "$ROOT/skills/token-trans/SKILL.md" "$TOKEN_TRANS_SKILL_DIR/SKILL.md"
  cp "$ROOT/skills/token-trans/agents/openai.yaml" "$TOKEN_TRANS_SKILL_DIR/agents/openai.yaml"
fi

if [ "$INSTALL_WRAPPER" -eq 1 ]; then
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
fi

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

python3 - "$MANIFEST" "$PLUGIN_HOME" "$SHIM" "$RC_FILE" "$rc_block_written" "$INSTALL_SKILL" "$TOKEN_TRANS_SKILL_DIR" "$INSTALL_WRAPPER" <<'PY'
import json, sys, time
manifest, home, shim, rc_file, rc_written, install_skill, token_trans_skill_dir, install_wrapper = sys.argv[1:]
managed_paths = [
    f"{home}/scripts/doctor.sh",
    f"{home}/scripts/uninstall.sh",
    f"{home}/.codex-plugin/plugin.json",
    f"{home}/skills/token-saver/SKILL.md",
]
if install_wrapper == "1":
    managed_paths.extend([
        f"{home}/scripts/codex-ts",
        f"{home}/scripts/token_saver.py",
        f"{home}/config.example.toml",
        shim,
    ])
user_preserved_paths = []
if install_wrapper == "1":
    user_preserved_paths.extend([
        f"{home}/config.toml",
        f"{home}/logs",
    ])
codex_skill_targets = []
if install_skill == "1":
    managed_paths.extend([
        f"{token_trans_skill_dir}/SKILL.md",
        f"{token_trans_skill_dir}/agents/openai.yaml",
    ])
    codex_skill_targets.append(token_trans_skill_dir)
data = {
    "tool": "codex-token-saver",
    "version": "0.2.0",
    "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "plugin_home": home,
    "wrapper_installed": install_wrapper == "1",
    "managed_paths": managed_paths,
    "codex_skill_targets": codex_skill_targets,
    "user_preserved_paths": user_preserved_paths,
    "shell_rc_file": rc_file if rc_written == "true" else None,
    "managed_rc_block": rc_written == "true",
}
with open(manifest, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY

if [ "$INSTALL_SKILL" -eq 1 ]; then
  skill_summary="$TOKEN_TRANS_SKILL_DIR
  Invoke with: \$token-trans <your non-English task>"
else
  skill_summary="skipped (--no-skill)"
fi

if [ "$INSTALL_WRAPPER" -eq 1 ]; then
  command_summary="$SHIM"
  path_summary="Added a managed block to $RC_FILE so new shells can run codex-ts directly.
  For this already-open shell, run: source \"$RC_FILE\""
  alias_summary="alias codex='$SHIM'"
  config_summary="$PLUGIN_HOME/config.toml"
  run_summary="codex-ts doctor"
else
  command_summary="skipped (--skill-only)"
  path_summary="skipped (--skill-only)"
  alias_summary="skipped (--skill-only)"
  config_summary="skipped (--skill-only)"
  run_summary="bash \"$PLUGIN_HOME/scripts/doctor.sh\""
fi

cat <<EOF
Codex Token Saver installed.

Command:
  $command_summary

Shell PATH:
  $path_summary

Optional alias, if you want codex to mean codex-ts:
  $alias_summary

Config:
  $config_summary

Skill:
  $skill_summary

Run:
  $run_summary
EOF
