---
name: token-saver
description: Use Codex Token Saver when a user wants Codex CLI prompts translated through a cheap model to reduce token cost, or wants to install, configure, diagnose, or uninstall the codex-ts wrapper.
---

# Codex Token Saver

Codex Token Saver provides a local wrapper command, `codex-ts`, that keeps the official `codex` installation untouched.

Use it when:

- The user wants prompts in any natural language translated to English before Codex CLI receives them.
- The user wants final Codex answers translated back to their original language.
- The user asks to diagnose or safely uninstall the wrapper.

Important behavior:

- `codex-ts exec` is the reliable path. It captures the final assistant message with `--output-last-message`, translates only that final message, and preserves the original exit code.
- Interactive TUI mode translates only the initial prompt and injects final-answer language guidance. Live streamed output filtering is best-effort until Codex exposes stable final-output hooks.
- If translation fails, the wrapper falls back to raw `codex`.
- The installer never overwrites official Codex binaries or unmanaged user files.

Typical commands:

```bash
./scripts/install.sh
codex-ts doctor
codex-ts exec "请帮我检查这个仓库的测试失败原因"
codex-ts exec "Por favor revisa por que fallan las pruebas"
./scripts/uninstall.sh --dry-run
```
