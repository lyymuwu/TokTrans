#!/usr/bin/env python3
"""Codex Token Saver.

This module intentionally uses only the Python standard library so the wrapper
can be installed from a Git checkout without dependency bootstrapping.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


PASSTHROUGH_COMMANDS = {
    "login",
    "logout",
    "mcp",
    "marketplace",
    "app",
    "completion",
    "sandbox",
    "debug",
    "apply",
    "cloud",
    "features",
    "help",
}

DEFAULT_CONFIG = {
    "enabled": True,
    "provider": "codex_cli",
    "model": "gpt-5-nano",
    "codex_model": "gpt-5.4-mini",
    "base_url": "https://api.openai.com/v1",
    "api_key_env": "OPENAI_API_KEY",
    "source_language": "auto",
    "target_language": "English",
    "min_non_english_ratio": 0.25,
    "mode": "auto",
    "detect_latin_languages": True,
    "translate_final_only": True,
    "fallback_on_error": "passthrough",
    "show_savings_report": True,
    "timeout_seconds": 45,
    "debug_save_text": False,
}


@dataclass
class Detection:
    should_translate: bool
    language: str
    non_english_ratio: float
    code_ratio: float
    reason: str


def plugin_home() -> Path:
    return Path(os.environ.get("CODEX_TOKEN_SAVER_HOME", "~/.codex-token-saver")).expanduser()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def config_path() -> Path:
    return Path(os.environ.get("CODEX_TOKEN_SAVER_CONFIG", str(plugin_home() / "config.toml"))).expanduser()


def load_config(path: Path | None = None) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    path = path or config_path()
    if path.exists():
        if tomllib is None:
            raise RuntimeError("Python 3.11+ is required to read TOML config")
        with path.open("rb") as f:
            loaded = tomllib.load(f)
        cfg.update(loaded)
    return cfg


def warn(message: str) -> None:
    print(f"codex-ts: {message}", file=sys.stderr)


def strip_protected_regions(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`\n]+`", " ", text)
    text = re.sub(r"(?m)^\s{4,}\S.*$", " ", text)
    text = re.sub(r"(?m)^\s*(\$|>|#)\s+\S.*$", " ", text)
    text = re.sub(r"(?m)^\s*[\{\[\]].*$", " ", text)
    return text


def estimate_code_ratio(text: str) -> float:
    if not text.strip():
        return 0.0
    protected = len(text) - len(strip_protected_regions(text))
    code_markers = len(re.findall(r"```|`|/[\w.-]+|[\w.-]+\.(py|js|ts|rs|go|json|toml|yaml|md)\b", text))
    ratio = protected / max(len(text), 1)
    return min(1.0, ratio + min(0.5, code_markers * 0.03))


def dominant_language(text: str) -> tuple[str, float]:
    sample = strip_protected_regions(text)
    letters = [c for c in sample if c.isalpha()]
    if not letters:
        return "unknown", 0.0
    counts = {
        "Chinese": 0,
        "Japanese": 0,
        "Korean": 0,
        "Thai": 0,
        "Arabic": 0,
        "Hindi": 0,
        "Cyrillic": 0,
        "Latin": 0,
        "Other": 0,
    }
    for c in letters:
        o = ord(c)
        if 0x4E00 <= o <= 0x9FFF:
            counts["Chinese"] += 1
        elif 0x3040 <= o <= 0x30FF:
            counts["Japanese"] += 1
        elif 0xAC00 <= o <= 0xD7AF:
            counts["Korean"] += 1
        elif 0x0E00 <= o <= 0x0E7F:
            counts["Thai"] += 1
        elif 0x0600 <= o <= 0x06FF:
            counts["Arabic"] += 1
        elif 0x0900 <= o <= 0x097F:
            counts["Hindi"] += 1
        elif 0x0400 <= o <= 0x04FF:
            counts["Cyrillic"] += 1
        elif "A" <= c <= "Z" or "a" <= c <= "z":
            counts["Latin"] += 1
        else:
            counts["Other"] += 1
    total = sum(counts.values())
    latin = counts["Latin"]
    non_english_ratio = 1.0 - (latin / max(total, 1))
    language = max((k for k in counts if k != "Latin"), key=lambda k: counts[k])
    if counts[language] == 0:
        language = "English"
    if language == "Cyrillic":
        language = "Russian"
    return language, non_english_ratio


def detect_language(text: str, cfg: dict | None = None) -> Detection:
    cfg = cfg or DEFAULT_CONFIG
    if not text.strip():
        return Detection(False, "unknown", 0.0, 0.0, "empty")
    code_ratio = estimate_code_ratio(text)
    language, non_english_ratio = dominant_language(text)
    threshold = float(cfg.get("min_non_english_ratio", 0.25))
    if code_ratio > 0.75:
        return Detection(False, language, non_english_ratio, code_ratio, "code-heavy")
    if language in {"English", "unknown"} or non_english_ratio < threshold:
        return Detection(False, language, non_english_ratio, code_ratio, "mostly-english")
    return Detection(True, language, non_english_ratio, code_ratio, "non-english")


def should_model_detect_language(text: str, detection: Detection, cfg: dict) -> bool:
    if not cfg.get("detect_latin_languages", True):
        return False
    if str(cfg.get("source_language", "auto")).lower() != "auto":
        return False
    if detection.should_translate or detection.reason != "mostly-english":
        return False
    if detection.code_ratio > 0.35:
        return False
    stripped = strip_protected_regions(text)
    letters = [c for c in stripped if c.isalpha()]
    if len(letters) < 12:
        return False
    latin_letters = [c for c in letters if ("A" <= c <= "Z") or ("a" <= c <= "z")]
    return len(latin_letters) / max(len(letters), 1) > 0.8


def parse_json_object(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def detect_language_with_model(text: str, cfg: dict) -> Detection:
    system = (
        "Detect the natural language of the user's request for a coding agent. "
        "Ignore code blocks, paths, commands, logs, JSON, identifiers, and quoted literals. "
        "Return strict JSON only with keys: language, should_translate, confidence. "
        "Set should_translate to true only when the natural-language request is not English."
    )
    user = f"Request:\n{text}"
    raw = translation_chat([{"role": "system", "content": system}, {"role": "user", "content": user}], cfg)
    payload = parse_json_object(raw)
    language = str(payload.get("language") or "unknown").strip() or "unknown"
    confidence = float(payload.get("confidence", 0))
    should_translate = bool(payload.get("should_translate")) and language.lower() != "english"
    base = detect_language(text, cfg)
    return Detection(should_translate, language, base.non_english_ratio, base.code_ratio, f"model-detect:{confidence:.2f}")


def resolve_detection(text: str, cfg: dict | None = None) -> Detection:
    cfg = cfg or DEFAULT_CONFIG
    source_language = str(cfg.get("source_language", "auto")).strip()
    base = detect_language(text, cfg)
    if source_language and source_language.lower() != "auto":
        if base.code_ratio > 0.75 or not text.strip():
            return base
        return Detection(source_language.lower() != "english", source_language, base.non_english_ratio, base.code_ratio, "configured")
    if should_model_detect_language(text, base, cfg):
        try:
            model_det = detect_language_with_model(text, cfg)
            if model_det.should_translate:
                return model_det
        except Exception as e:
            warn(f"language auto-detection failed, using heuristic: {e}")
    return base


def rough_token_estimate(text: str) -> int:
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    non_ascii = len(text) - ascii_chars
    return max(1, round(ascii_chars / 4 + non_ascii * 1.2))


def openai_chat(messages: list[dict], cfg: dict) -> str:
    api_key = os.environ.get(str(cfg.get("api_key_env", "OPENAI_API_KEY")))
    if not api_key:
        raise RuntimeError(f"missing API key env {cfg.get('api_key_env', 'OPENAI_API_KEY')}")
    base_url = str(cfg.get("base_url", "https://api.openai.com/v1")).rstrip("/")
    body = {
        "model": cfg.get("model", "gpt-5-nano"),
        "messages": messages,
        "temperature": 0,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=float(cfg.get("timeout_seconds", 45))) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"translation API HTTP {e.code}: {detail}") from e
    return payload["choices"][0]["message"]["content"]


def codex_cli_chat(messages: list[dict], cfg: dict) -> str:
    codex = find_real_codex()
    prompt_parts = [
        "You are a translation engine used by Codex Token Saver.",
        "Follow the system and user instructions below. Return only the requested translation.",
        "",
    ]
    for message in messages:
        role = str(message.get("role", "user")).upper()
        content = str(message.get("content", ""))
        prompt_parts.append(f"{role}:\n{content}\n")
    prompt = "\n".join(prompt_parts)

    with tempfile.TemporaryDirectory(prefix="codex-ts-translate-") as tmp:
        final_path = Path(tmp) / "translation.txt"
        command = [codex, "exec"]
        codex_model = str(cfg.get("codex_model", "")).strip()
        if codex_model:
            command += ["-m", codex_model]
        command += [
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--output-last-message",
            str(final_path),
            prompt,
        ]
        try:
            result = run_child(
                command,
                stdin_text=None,
                capture=True,
                timeout=float(cfg.get("timeout_seconds", 45)),
            )
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"codex_cli translation timed out after {e.timeout:.0f}s") from e
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()[:500]
            raise RuntimeError(f"codex_cli translation failed ({result.returncode}): {detail}")
        if final_path.exists():
            return final_path.read_text(encoding="utf-8")
        return result.stdout


def translation_chat(messages: list[dict], cfg: dict) -> str:
    provider = str(cfg.get("provider", "openai")).lower().replace("-", "_")
    if provider in {"openai", "openai_compatible"}:
        return openai_chat(messages, cfg)
    if provider in {"codex", "codex_cli"}:
        return codex_cli_chat(messages, cfg)
    raise RuntimeError(f"unsupported provider: {cfg.get('provider')}")


def translate_to_english(text: str, language: str, cfg: dict) -> str:
    system = (
        "Translate user instructions into concise English for a coding agent. "
        "Preserve code blocks, inline code, commands, paths, URLs, JSON/YAML/TOML, "
        "tables, stack traces, quoted literals, identifiers, and markdown structure exactly. "
        "Return only the translated prompt."
    )
    user = f"Source language: {language}\n\n{text}"
    return translation_chat([{"role": "system", "content": system}, {"role": "user", "content": user}], cfg).strip()


def translate_from_english(text: str, target_language: str, cfg: dict) -> str:
    system = (
        "Translate the final assistant answer into the requested target language. "
        "Do not translate code blocks, inline code, commands, paths, API names, file names, "
        "identifiers, or quoted literals. Preserve markdown formatting. Return only the translation."
    )
    user = f"Target language: {target_language}\n\n{text}"
    return translation_chat([{"role": "system", "content": system}, {"role": "user", "content": user}], cfg).strip()


def find_real_codex(self_path: Path | None = None) -> str:
    env_path = os.environ.get("CODEX_TOKEN_SAVER_REAL_CODEX")
    if env_path:
        p = Path(env_path).expanduser()
        if p.exists() and os.access(p, os.X_OK):
            return str(p)
        raise RuntimeError(f"CODEX_TOKEN_SAVER_REAL_CODEX is not executable: {p}")

    self_path = (self_path or Path(sys.argv[0])).resolve()
    candidates: list[Path] = []
    for part in os.environ.get("PATH", "").split(os.pathsep):
        if not part:
            continue
        for name in ("codex", "codex.cmd", "codex.exe"):
            p = Path(part) / name
            if p.exists() and os.access(p, os.X_OK):
                try:
                    if p.resolve() == self_path:
                        continue
                except OSError:
                    pass
                candidates.append(p)
    if candidates:
        return str(candidates[0])

    common = [
        Path("/opt/homebrew/bin/codex"),
        Path("/usr/local/bin/codex"),
        Path("/Applications/Codex.app/Contents/Resources/codex"),
    ]
    for p in common:
        if p.exists() and os.access(p, os.X_OK):
            return str(p)
    raise RuntimeError("could not find real codex; set CODEX_TOKEN_SAVER_REAL_CODEX")


def is_passthrough(args: Sequence[str]) -> bool:
    if not args:
        return False
    if any(a in {"-h", "--help", "-V", "--version"} for a in args):
        return True
    first = next((a for a in args if not a.startswith("-")), "")
    return first in PASSTHROUGH_COMMANDS


def split_exec_prompt(args: list[str], stdin_text: str | None) -> tuple[list[str], str, bool]:
    """Return args-without-prompt, prompt, read_from_stdin flag for `codex exec`."""
    if args and args[0] in {"exec", "e"}:
        rest = args[1:]
        prefix = [args[0]]
    else:
        rest = args
        prefix = ["exec"]

    prompt_index = None
    skip_next = False
    options_with_values = {
        "-c", "--config", "-i", "--image", "-m", "--model", "-s", "--sandbox",
        "-p", "--profile", "-C", "--cd", "--add-dir", "--output-schema",
        "--color", "-o", "--output-last-message",
    }
    for i, a in enumerate(rest):
        if skip_next:
            skip_next = False
            continue
        if a == "--":
            prompt_index = i + 1 if i + 1 < len(rest) else None
            break
        if a in options_with_values:
            skip_next = True
            continue
        if a == "-":
            prompt_index = i
            break
        if a.startswith("-"):
            continue
        if a in {"resume", "review", "help"}:
            return args, "", False
        prompt_index = i
        break

    read_from_stdin = False
    if prompt_index is None:
        prompt = stdin_text or ""
        read_from_stdin = bool(stdin_text)
        return prefix + rest, prompt, read_from_stdin
    prompt = rest[prompt_index]
    if prompt == "-":
        prompt = stdin_text or ""
        read_from_stdin = True
        new_rest = rest[:prompt_index] + rest[prompt_index + 1 :]
    else:
        new_rest = rest[:prompt_index] + rest[prompt_index + 1 :]
        if stdin_text:
            prompt = prompt + "\n\n<stdin>\n" + stdin_text + "\n</stdin>"
    return prefix + new_rest, prompt, read_from_stdin


def inject_output_file(args: list[str], output_path: Path) -> tuple[list[str], Path | None]:
    user_output: Path | None = None
    out = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in {"-o", "--output-last-message"} and i + 1 < len(args):
            user_output = Path(args[i + 1]).expanduser()
            i += 2
            continue
        if a.startswith("--output-last-message="):
            user_output = Path(a.split("=", 1)[1]).expanduser()
            i += 1
            continue
        out.append(a)
        i += 1
    return out + ["--output-last-message", str(output_path)], user_output


def run_child(
    command: list[str],
    *,
    stdin_text: str | None,
    capture: bool,
    timeout: float | None = None,
) -> subprocess.CompletedProcess:
    if capture:
        stdin = subprocess.DEVNULL if stdin_text is None else None
        return subprocess.run(
            command,
            input=stdin_text,
            stdin=stdin,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    proc = subprocess.Popen(command, stdin=subprocess.PIPE if stdin_text is not None else None)

    def forward(sig, _frame):
        try:
            proc.send_signal(sig)
        except ProcessLookupError:
            pass

    old_int = signal.signal(signal.SIGINT, forward)
    old_term = signal.signal(signal.SIGTERM, forward)
    try:
        proc.communicate(stdin_text)
    finally:
        signal.signal(signal.SIGINT, old_int)
        signal.signal(signal.SIGTERM, old_term)
    return subprocess.CompletedProcess(command, proc.returncode)


def run_raw(args: list[str]) -> int:
    codex = find_real_codex()
    return run_child([codex] + args, stdin_text=None, capture=False).returncode or 0


def handle_exec(args: list[str], cfg: dict, stdin_text: str | None) -> int:
    codex = find_real_codex()
    base_args, prompt, _ = split_exec_prompt(args, stdin_text)
    detection = resolve_detection(prompt, cfg)
    if not cfg.get("enabled", True) or not detection.should_translate:
        return run_child([codex] + args, stdin_text=stdin_text, capture=False).returncode or 0

    try:
        translated = translate_to_english(prompt, detection.language, cfg)
    except Exception as e:
        warn(f"translation failed, falling back to raw codex: {e}")
        return run_child([codex] + args, stdin_text=stdin_text, capture=False).returncode or 0

    with tempfile.TemporaryDirectory(prefix="codex-ts-") as tmp:
        final_path = Path(tmp) / "final.md"
        exec_args, user_output = inject_output_file(base_args, final_path)
        command = [codex] + exec_args + [translated]
        start = time.time()
        try:
            result = run_child(
                command,
                stdin_text=None,
                capture=True,
                timeout=float(cfg.get("timeout_seconds", 45)),
            )
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"codex_cli translation timed out after {e.timeout:.0f}s") from e
        elapsed = time.time() - start
        if result.stderr:
            sys.stderr.write(result.stderr)
        final_text = final_path.read_text(encoding="utf-8") if final_path.exists() else result.stdout
        try:
            translated_final = translate_from_english(final_text, detection.language, cfg).strip()
        except Exception as e:
            warn(f"final translation failed, showing original final answer: {e}")
            translated_final = final_text
        if translated_final:
            print(translated_final)
        if user_output:
            user_output.parent.mkdir(parents=True, exist_ok=True)
            user_output.write_text(translated_final, encoding="utf-8")
        if cfg.get("show_savings_report", True):
            before = rough_token_estimate(prompt)
            after = rough_token_estimate(translated)
            delta = before - after
            warn(
                f"estimated prompt tokens {before} -> {after} ({delta:+d}); "
                f"language={detection.language}; elapsed={elapsed:.1f}s"
            )
        return result.returncode or 0


def handle_tui(args: list[str], cfg: dict) -> int:
    codex = find_real_codex()
    if not args:
        return run_child([codex], stdin_text=None, capture=False).returncode or 0
    prompt = args[-1] if not args[-1].startswith("-") else ""
    detection = resolve_detection(prompt, cfg)
    if not cfg.get("enabled", True) or not detection.should_translate:
        return run_child([codex] + args, stdin_text=None, capture=False).returncode or 0
    try:
        translated = translate_to_english(prompt, detection.language, cfg)
    except Exception as e:
        warn(f"translation failed, falling back to raw codex: {e}")
        return run_child([codex] + args, stdin_text=None, capture=False).returncode or 0
    new_args = args[:-1] + [translated]
    warn("interactive mode translates the initial prompt only; final-output translation is best-effort")
    return run_child([codex] + new_args, stdin_text=None, capture=False).returncode or 0


def doctor() -> int:
    ok = True
    try:
        cfg = load_config()
        print(f"config: ok ({config_path()})")
    except Exception as e:
        print(f"config: failed ({e})")
        return 1
    try:
        codex = find_real_codex()
        print(f"real codex: ok ({codex})")
    except Exception as e:
        print(f"real codex: failed ({e})")
        ok = False
    provider = str(cfg.get("provider", "codex_cli")).lower().replace("-", "_")
    if provider in {"codex", "codex_cli"}:
        model = str(cfg.get("codex_model", "gpt-5.4-mini") or "default")
        print(f"translation provider: codex_cli (model={model}, uses Codex login/quota)")
    else:
        api_env = str(cfg.get("api_key_env", "OPENAI_API_KEY"))
        if os.environ.get(api_env):
            print(f"credentials: ok ({api_env})")
        else:
            print(f"credentials: missing ({api_env})")
            ok = False
    manifest = plugin_home() / "install-manifest.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            print(f"install manifest: ok ({len(data.get('managed_paths', []))} paths)")
        except Exception as e:
            print(f"install manifest: invalid ({e})")
            ok = False
    else:
        print("install manifest: missing (normal before install)")
    sample = "请用一句话说明这个项目的作用"
    det = resolve_detection(sample, cfg)
    print(f"language detection: {det.language}, translate={det.should_translate}, ratio={det.non_english_ratio:.2f}")
    if provider in {"codex", "codex_cli"} or os.environ.get(str(cfg.get("api_key_env", "OPENAI_API_KEY"))):
        try:
            translated = translate_to_english(sample, det.language, cfg)
            print(f"dry-run translation: ok ({translated[:80]})")
        except Exception as e:
            print(f"dry-run translation: failed ({e})")
            ok = False
    return 0 if ok else 1


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if argv and argv[0] == "run":
        args = argv[1:]
        if args and args[0] == "doctor":
            return doctor()
        if is_passthrough(args):
            return run_raw(args)
        try:
            cfg = load_config()
        except Exception as e:
            warn(f"could not read config, falling back to raw codex: {e}")
            return run_raw(args)
        stdin_text = None
        if not sys.stdin.isatty():
            stdin_text = sys.stdin.read()
        first = next((a for a in args if not a.startswith("-")), "")
        if first in {"exec", "e"} or (not first and stdin_text):
            return handle_exec(args or ["exec"], cfg, stdin_text)
        return handle_tui(args, cfg)

    parser = argparse.ArgumentParser(prog="token_saver.py")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("doctor")
    ns = parser.parse_args(argv)
    if ns.command == "doctor":
        return doctor()
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
