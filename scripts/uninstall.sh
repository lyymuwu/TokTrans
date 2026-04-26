#!/usr/bin/env bash
set -euo pipefail

PLUGIN_HOME="${CODEX_TOKEN_SAVER_HOME:-$HOME/.codex-token-saver}"
MANIFEST="$PLUGIN_HOME/install-manifest.json"
DRY_RUN=0
PURGE=0
YES=0

usage() {
  cat <<'USAGE'
Usage: scripts/uninstall.sh [--dry-run] [--purge] [--yes]

Safely removes only files recorded in install-manifest.json.

Options:
  --dry-run  Print removals without deleting.
  --purge    Remove plugin home after managed files are removed. Requires --yes.
  --yes      Confirm purge.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --purge) PURGE=1 ;;
    --yes) YES=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [ ! -f "$MANIFEST" ]; then
  echo "No install manifest found: $MANIFEST" >&2
  exit 1
fi

python3 - "$MANIFEST" "$PLUGIN_HOME" "$DRY_RUN" "$PURGE" "$YES" <<'PY'
import json, os, shutil, sys
from pathlib import Path

manifest = Path(sys.argv[1]).expanduser().resolve()
home = Path(sys.argv[2]).expanduser().resolve()
dry_run = sys.argv[3] == "1"
purge = sys.argv[4] == "1"
yes = sys.argv[5] == "1"

data = json.loads(manifest.read_text(encoding="utf-8"))
if data.get("tool") != "codex-token-saver":
    raise SystemExit("Manifest is not for codex-token-saver")

def allowed(path: Path) -> bool:
    path = path.expanduser().resolve()
    if home in path.parents or path == home:
        return True
    if path.name == "codex-ts" and ".local" in path.parts:
        return True
    return False

def remove_path(raw: str) -> None:
    path = Path(raw).expanduser()
    resolved = path.resolve() if path.exists() or path.is_symlink() else path
    if not allowed(resolved):
        print(f"refuse: outside allowed locations: {path}")
        return
    if not path.exists() and not path.is_symlink():
        print(f"skip: {path}")
        return
    print(f"remove: {path}")
    if dry_run:
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()

for raw in data.get("managed_paths", []):
    remove_path(raw)

rc = data.get("shell_rc_file")
if rc and data.get("managed_rc_block"):
    rc_path = Path(rc).expanduser()
    begin = "# >>> codex-token-saver managed block >>>"
    end = "# <<< codex-token-saver managed block <<<"
    if rc_path.exists():
        text = rc_path.read_text(encoding="utf-8")
        start = text.find(begin)
        finish = text.find(end)
        if start != -1 and finish != -1 and finish > start:
            finish += len(end)
            print(f"remove managed rc block: {rc_path}")
            if not dry_run:
                rc_path.write_text(text[:start].rstrip() + "\n" + text[finish:].lstrip(), encoding="utf-8")

if manifest.exists():
    print(f"remove: {manifest}")
    if not dry_run:
        manifest.unlink()

if purge:
    if not yes:
        raise SystemExit("--purge requires --yes")
    if home.exists():
        print(f"purge: {home}")
        if not dry_run:
            shutil.rmtree(home)
else:
    print(f"preserve: {home}/config.toml and logs")
PY
