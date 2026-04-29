# Codex Token Saver

[![CI](https://github.com/lyymuwu/codex-token-saver/actions/workflows/ci.yml/badge.svg)](https://github.com/lyymuwu/codex-token-saver/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Codex CLI](https://img.shields.io/badge/Codex-CLI-111827)](https://github.com/openai/codex)

**Think in English. Work in any language. Spend the strongest model where it matters.**

Codex Token Saver gives you two ways to run non-English Codex work through an English reasoning path:

- `$token-trans`: the recommended Codex skill for in-app agent workflows.
- `codex-ts`: a safe Codex CLI wrapper for terminal automation and `codex exec`.

Both follow the same principle: translate the user request to English with a cheaper model, let the main agent work in English, then translate only the final answer back.

![Codex Token Saver workflow](docs/hero.svg)

## Recommended Install: Skill First

```bash
curl -fsSL https://raw.githubusercontent.com/lyymuwu/codex-token-saver/main/scripts/bootstrap.sh | bash -s -- --skill-only
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
curl -fsSL https://raw.githubusercontent.com/lyymuwu/codex-token-saver/main/scripts/bootstrap.sh | bash
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
curl -fsSL https://raw.githubusercontent.com/lyymuwu/codex-token-saver/main/scripts/bootstrap.sh | bash -s -- --no-skill
```

Inspect-first install:

```bash
git clone https://github.com/lyymuwu/codex-token-saver.git
cd codex-token-saver
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

Use `$token-trans` first when you are already inside Codex and want a specific non-English task to go through cheap translation subagents:

```text
$token-trans 帮我检查Server.md中的A100_1中几个/data, /data2, /data2_remote几个盘分别挂载到哪里的，是本地设备还是远程其他服务器上的
```

Use the bare form above. Avoid Markdown-link activation such as:

```text
[$token-trans](/path/to/SKILL.md) ...
```

The skill is intentionally explicit opt-in. Short chats and ordinary translation requests should not pay the extra subagent overhead.

## How It Works

```text
non-English task
      |
      v
cheap translator -> English task
      |
      v
main Codex work in English
      |
      v
cheap translator -> final answer in original language
```

For the skill path, intermediate work and progress stay in English. Only the final response is translated back.

## Why This Is Interesting

Many tokenizers spend more visible tokens on Chinese, Japanese, Thai, Hindi, Arabic, and other non-English prompts than on equivalent English prompts. More importantly, many coding, ops, and research tasks have stronger model coverage in English.

This project exploits that asymmetry without forcing users to write English. The expensive model receives a cleaner English task; the user still gets the final answer in their language.

It is not magic. Hidden reasoning tokens are not visible to the wrapper, translation adds latency, and one-line prompts may cost more than they save. The target use case is long, technical, non-English work: debugging, code review, server ops, experiment planning, research notes, and refactors.

## Evidence

The claim is not that English always wins. The practical claim is narrower: for many current LLM workflows, translating a non-English task into English before the expensive reasoning step is a strong default to test.

| Source | Reported finding | Why it matters here |
|---|---|---|
| [Etxaniz et al., “Do Multilingual Language Models Think Better in English?”, NAACL 2024](https://aclanthology.org/2024.naacl-short.46/) | Their self-translate method consistently outperforms direct non-English inference across 5 multilingual tasks. | Supports the core `$token-trans` idea: use a cheap translation boundary, then let the main model solve the task in English. |
| [Ahuja et al., “MEGAVERSE: Benchmarking Large Language Models Across Languages, Modalities, Models and Tasks”, NAACL 2024](https://aclanthology.org/2024.naacl-long.143/) | Benchmarks LLMs across 22 datasets and 83 languages, highlighting non-English capability gaps, especially for lower-resource languages. | Treats multilingual parity as an empirical question, not an assumption; English-centered workflows can still be a useful fallback. |
| [Petrov et al., “Language Model Tokenizers Introduce Unfairness Between Languages”, NeurIPS 2023](https://proceedings.neurips.cc/paper_files/paper/2023/hash/74bb24dca8334adce292883b4b651eda-Abstract-Conference.html) | The same text translated into different languages can have drastically different tokenization lengths, with reported differences up to 15x. | Supports the cost/context-pressure side of Token Saver: language choice can affect visible prompt length before reasoning even starts. |

Operational takeaway:

| Prompt type | Recommended path | Reason |
|---|---|---|
| Long non-English coding/research task inside Codex | `$token-trans ...` | Native skill, cheap translation subagents, main work in English, final answer back. |
| Terminal automation or CI-style `codex exec` | `codex-ts exec "..."` | Wrapper captures final output and can report visible-token estimates. |
| Short one-line chat | Plain Codex | Two translation calls may cost more than they save. |
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
~/.codex-token-saver/config.toml
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

Visible-token estimates are heuristic. They do not measure hidden reasoning tokens or backend billing internals. See [docs/benchmark.md](docs/benchmark.md) for benchmark snapshots.

## Uninstall

Preview:

```bash
~/.codex-token-saver/scripts/uninstall.sh --dry-run
```

Remove managed files:

```bash
~/.codex-token-saver/scripts/uninstall.sh
```

Purge the plugin home too:

```bash
~/.codex-token-saver/scripts/uninstall.sh --purge --yes
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
