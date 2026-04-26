# Contributing

Thanks for helping make Codex Token Saver better.

## Local Checks

```bash
python3 -m unittest discover -s tests
shellcheck scripts/*.sh scripts/codex-ts
```

## Design Rules

- Keep the official `codex` binary untouched.
- Preserve pass-through behavior for login, help, marketplace, and other non-prompt commands.
- Prefer conservative translation. Code-heavy prompts should pass through unchanged.
- Do not log prompt text unless the user explicitly sets `debug_save_text = true`.
- Installer and uninstaller changes must remain idempotent and manifest-driven.

## Good First Issues

- Improve language detection samples.
- Add fake-Codex integration tests for more CLI argument combinations.
- Document real-world token savings for different language pairs.
