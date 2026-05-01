# TokTrans

[![CI](https://github.com/lyymuwu/TokTrans/actions/workflows/ci.yml/badge.svg)](https://github.com/lyymuwu/TokTrans/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Codex CLI](https://img.shields.io/badge/Codex-CLI-111827)](https://github.com/openai/codex)

**Translate the tokens around Codex without changing how Codex itself is installed.**

TokTrans provides a small translation layer for Codex workflows. It is not a replacement for Codex and it does not patch the official `codex` binary; it only translates the user-facing text that enters or leaves a Codex run when you explicitly opt in.

TokTrans currently ships two entry points:

- `$token-trans`: the recommended Codex skill for in-app agent workflows.
- `codex-ts`: a safe Codex CLI wrapper for terminal automation and `codex exec`.

Both follow the same principle: translate the request before Codex receives it, then translate only the final answer back for the user. The purpose of this repository is token translation, not a promise of token savings.

![TokTrans workflow](docs/hero.svg)

## Recommended Install: Skill First

```bash
curl -fsSL https://raw.githubusercontent.com/lyymuwu/TokTrans/main/scripts/bootstrap.sh | bash -s -- --skill-only
```

This installs only the native Codex skill:

```text
${CODEX_HOME:-$HOME/.codex}/skills/token-trans
```

Use it inside Codex:

```text
$token-trans 帮我检查这个项目为什么测试失败
```

The skill path is recommended because it is explicit, lightweight, and does not wrap the `codex` binary or modify your shell PATH.

## Full Install: Skill + Wrapper

Use this if you also want the terminal wrapper command `codex-ts`:

```bash
curl -fsSL https://raw.githubusercontent.com/lyymuwu/TokTrans/main/scripts/bootstrap.sh | bash
```

Then open a new shell or run:

```bash
source ~/.zshrc
codex-ts doctor
```

Full install sets up both:

- Wrapper: `~/.local/bin/codex-ts`
- Skill: `${CODEX_HOME:-$HOME/.codex}/skills/token-trans`

Wrapper-only install:

```bash
curl -fsSL https://raw.githubusercontent.com/lyymuwu/TokTrans/main/scripts/bootstrap.sh | bash -s -- --no-skill
```

Inspect-first install:

```bash
git clone https://github.com/lyymuwu/TokTrans.git
cd TokTrans
./scripts/install.sh
```

## Use The Wrapper

Use `codex-ts` when you want terminal automation, shell pipelines, or a drop-in command around `codex exec`:

```bash
codex-ts exec "请帮我检查这个仓库为什么测试失败"
codex-ts exec "このプロジェクトのREADMEをもっと魅力的にして"
echo "请总结这个错误日志" | codex-ts exec -
codex-ts "请帮我修改这个项目的 README"
```

Pass-through commands keep normal Codex behavior:

```bash
codex-ts --version
codex-ts --help
codex-ts login
```

If you want `codex` itself to mean `codex-ts`, opt in explicitly:

```bash
./scripts/install.sh --alias
```

## Use The Skill

Use `$token-trans` first when you are already inside Codex and want a specific task to go through translation subagents:

```text
$token-trans 帮我检查 Server.md 中 A100_1 的 /data、/data2、/data2_remote 分别挂载到哪里
```

Use the bare form above. Avoid Markdown-link activation such as:

```text
[$token-trans](/path/to/SKILL.md) ...
```

The skill is intentionally explicit opt-in. Use it when you want a Codex task to pass through the TokTrans translation layer.

## How It Works

```text
user task
      |
      v
translator -> Codex-ready task
      |
      v
main Codex work
      |
      v
translator -> final answer in the user's language
```

For the skill path, intermediate work and progress stay in the main agent's working language. Only the final response is translated back.

## Why This Exists

Codex tasks often contain a mix of natural language, code, paths, logs, stack traces, and structured data. TokTrans focuses on translating only the natural-language parts around that workflow while preserving the technical tokens that should stay stable.

This repository is intentionally narrow: it provides a translation adapter for Codex skills and CLI automation. Any token-count reduction is a possible side effect of translation, not the main product claim.

It is not magic. Translation adds latency, may fail, and may be unnecessary for short or code-heavy prompts. The target use case is technical multilingual work where the user wants a consistent translation boundary around Codex.

## Scope

Operational guidance:

| Prompt type | Recommended path | Reason |
|---|---|---|
| Multilingual coding/research task inside Codex | `$token-trans ...` | Native skill, explicit translation boundary, final answer back. |
| Terminal automation or CI-style `codex exec` | `codex-ts exec "..."` | Wrapper captures final output and can translate it back. |
| Short one-line chat | Plain Codex | A translation layer may add unnecessary overhead. |
| Code-heavy prompt with little natural language | Plain Codex or wrapper auto-pass-through | Code, paths, and logs are already mostly language-neutral. |

## Safety Model

- The official `codex` binary is never patched or replaced.
- `codex-ts` is a separate wrapper command.
- `$token-trans` uses `fork_context: false` for translator subagents.
- Translation prompts preserve code blocks, paths, commands, stack traces, URLs, JSON/YAML/TOML, and quoted literals.
- The skill tells translator subagents not to receive repository history, files, credentials, API keys, or unrelated context.
- If translation fails, the wrapper falls back to raw Codex and the skill continues without token-trans.

## Configuration

Default wrapper config lives at:

```text
~/.toktrans/config.toml
```

Default values:

```toml
enabled = true
provider = "codex_cli"
model = "gpt-5-nano"
codex_model = "gpt-5.4-mini"
base_url = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"
source_language = "auto"
target_language = "English"
min_non_english_ratio = 0.25
mode = "auto"
detect_latin_languages = true
translate_final_only = true
fallback_on_error = "passthrough"
show_savings_report = true
timeout_seconds = 45
debug_save_text = false
```

`provider = "codex_cli"` reuses your Codex account and quota. To use an OpenAI-compatible endpoint instead:

```toml
provider = "openai"
model = "gpt-5-nano"
base_url = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"
```

Then set:

```bash
export OPENAI_API_KEY="..."
```

## Verify

```bash
codex-ts doctor
python3 -m unittest discover -s tests
```

The wrapper prints visible-token estimates for translated `codex exec` prompts, for example:

```text
codex-ts: estimated prompt tokens 120 -> 78 (-42); language=Chinese; elapsed=12.4s
```

Visible-token estimates are heuristic. They are shown only as debugging information for wrapper runs and are not the primary purpose of TokTrans.

## Uninstall

Preview:

```bash
~/.toktrans/scripts/uninstall.sh --dry-run
```

Remove managed files:

```bash
~/.toktrans/scripts/uninstall.sh
```

Purge the plugin home too:

```bash
~/.toktrans/scripts/uninstall.sh --purge --yes
```

The uninstaller removes only manifest-managed files. It preserves config and logs unless `--purge --yes` is used.

## Repository Layout

```text
.
├── scripts/
│   ├── codex-ts              # wrapper entry
│   ├── token_saver.py        # translation and Codex orchestration
│   ├── install.sh            # installs wrapper + skill by default
│   └── uninstall.sh
├── skills/
│   ├── token-saver/          # wrapper management skill
│   └── token-trans/          # explicit Codex translation skill
├── tests/
└── docs/
```

## Development

```bash
python3 -m unittest discover -s tests
shellcheck scripts/*.sh scripts/codex-ts
python3 scripts/benchmark_visible_tokens.py
```

Release artifacts should include repository files only. Never bundle local config, logs, tokens, `.env` files, or `install-manifest.json`.

## License

MIT
