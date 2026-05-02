# TokTrans

[![CI](https://github.com/lyymuwu/TokTrans/actions/workflows/ci.yml/badge.svg)](https://github.com/lyymuwu/TokTrans/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Codex CLI](https://img.shields.io/badge/Codex-CLI-111827)](https://github.com/openai/codex)
[![Claude Code](https://img.shields.io/badge/Claude-Code-CC785C)](https://docs.claude.com/en/docs/claude-code/overview)

<p align="center">
  <strong>When your coding agent feels weaker outside English, it may not be your prompt. It may be the language.</strong>
</p>

<p align="center">
  <em>TokTrans ships native skills for <strong>Codex</strong> and <strong>Claude Code</strong>. Pick the one that matches your workflow.</em>
</p>

<table>
  <tr>
    <td width="50%">
      <h3>The agent feels less sharp?</h3>
      <p>Same repo, same bug, same intent, but the answer misses context or needs more back-and-forth when the task is not written in English.</p>
    </td>
    <td width="50%">
      <h3>Your quota vanishes too fast?</h3>
      <p>Some languages spend more visible tokens before reasoning even starts, leaving less room for the actual task.</p>
    </td>
  </tr>
</table>

TokTrans adds an explicit translation layer for your coding agent. It translates the user-facing text that enters or leaves an agent run while preserving code, paths, logs, commands, stack traces, JSON/YAML/TOML, and quoted literals.

It does not replace the agent, patch any official binary, or force you to work in English. You keep writing in your language; the agent gets a cleaner task; the final answer comes back in your language. The same translation protocol is shipped as a skill for both **Codex** and **Claude Code**.

<p align="center">
  <strong>Try it on one real multilingual debugging task. If it saves you a round trip, a star helps more developers find it.</strong>
</p>

## Evidence

Tokenizer behavior is not language-neutral. Aran Komatsuzaki's tokenizer experiment uses English as the 1x baseline and shows that non-English prompts can consume substantially more tokens. TestingCatalog's write-up reports that Chinese, Japanese, and Hindi use 44% to 65% more tokens than English in Claude 3.7 Sonnet, while tokenizers optimized for Asian languages behave very differently.

<p align="center">
  <a href="https://x.com/arankomatsuzaki/status/2049177688402022730">
    <img src="https://testingcatalog.net/wp-content/uploads/2026/04/1777451082-paste_20260429_162259_971223.webp" alt="Tokenizer comparison across languages and model families" width="780">
  </a>
</p>

Source: [Aran Komatsuzaki on X](https://x.com/arankomatsuzaki/status/2049177688402022730), with an accessible summary in [TestingCatalog](https://testingcatalog.net/claudes-65-token-premium-for-chinese-is-a-hard-lesson-in-tokenizer-bias/).

Quality is affected too. [CodeMixBench](https://arxiv.org/abs/2505.05063) (2025) evaluates code generation on English-only prompts versus controlled code-mixed prompts built from BigCodeBench. In the figure below, the red dashed line is the original English prompt baseline, while the blue and green lines are code-mixed prompts. Most blue/green points sit below the red baseline, showing that mixed-language instructions often reduce Pass@1 even when the underlying programming task is the same.

![CodeMixBench Pass@1 comparison across English and code-mixed prompts](docs/codemixbench-pass1.png)

Figure source: CodeMixBench, Figure 1.

[When Models Reason in Your Language](https://arxiv.org/abs/2505.22888) (EMNLP Findings 2025) studies large reasoning models on multilingual math and science questions. The figure below has two stories:

- The top row measures whether the model's hidden thinking trace matches the requested language. Stronger language-control prompting raises the average matching rate from 46% to 98%.
- The bottom row measures answer accuracy on the same setting. That stronger language control drops average accuracy from 26% to 17%.

This is the trade-off TokTrans is designed around: forcing the model to reason in the user's language can make the trace more readable, but it can also make the answer worse. TokTrans instead takes the pragmatic path: translate the task into an agent-ready form, preserve technical tokens, let the model work in its stronger reasoning regime, then translate only the final answer back.

![Language matching and answer accuracy trade-off from When Models Reason in Your Language](docs/reasoning-language-accuracy.png)

Figure source: When Models Reason in Your Language, Figure 2.

TokTrans exists because multilingual technical work needs a practical translation layer, not because every task should be translated. The impact depends on the model, tokenizer, language, and task.

## What You Get

- `$token-trans` skill for **Codex** — explicit opt-in skill for in-app agent workflows.
- `$token-trans` skill for **Claude Code** — same protocol, ported to Claude Code's native subagent system (`Task` + `model: haiku`).
- `codex-ts`: a safe wrapper for terminal automation and `codex exec` (Codex only).
- Technical-token preservation for code, paths, logs, stack traces, commands, and structured data.
- Final-answer translation back into the user's language.
- No patching or replacement of the official `codex` or `claude` binaries.

![TokTrans workflow](docs/hero.svg)

## Pick Your Platform

Both skills follow the same 3-step translation protocol — translate inbound, work in English, translate outbound — and use a low-cost translator subagent on each end with no repository or secret context. Choose the one that matches your tool:

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>Codex</h3>
      <p>Skill installs to <code>~/.codex/skills/token-trans/</code> and uses the cheapest Codex subagent (e.g. <code>gpt-5.4-mini</code>) for translations. Optional <code>codex-ts</code> CLI wrapper available.</p>
      <p>Skill source: <code>skills/token-trans/SKILL.md</code></p>
    </td>
    <td width="50%" valign="top">
      <h3>Claude Code</h3>
      <p>Skill installs to <code>~/.claude/skills/token-trans/</code> and uses Claude Code's <code>Task</code> tool with <code>model: "haiku"</code> for translations. No CLI wrapper needed.</p>
      <p>Skill source: <code>skills/claude-code/token-trans/SKILL.md</code></p>
    </td>
  </tr>
</table>

## Quick Start — Codex

Install only the native Codex skill:

```bash
curl -fsSL https://raw.githubusercontent.com/lyymuwu/TokTrans/main/scripts/bootstrap.sh | bash -s -- --skill-only
```

Use it inside Codex:

```text
$token-trans 帮我检查这个项目为什么测试失败
```

The skill path is explicit, lightweight, and does not wrap `codex` or modify your shell PATH.

## Quick Start — Claude Code

Clone the repo and install the Claude Code skill into `~/.claude/skills/token-trans/`:

```bash
git clone https://github.com/lyymuwu/TokTrans.git
cd TokTrans
bash scripts/install-claude-code.sh
```

Use it inside Claude Code:

```text
$token-trans 帮我检查这个项目为什么测试失败
```

Claude Code matches the skill on `$token-trans`, then spawns short-lived `Task` subagents on `model: haiku` to translate the request to English and the final answer back. Main work happens on your normal Claude Code model in English.

To uninstall, just remove the skill folder:

```bash
rm -rf ~/.claude/skills/token-trans
```

## Optional Codex CLI Wrapper

Install the Codex skill plus `codex-ts`:

```bash
curl -fsSL https://raw.githubusercontent.com/lyymuwu/TokTrans/main/scripts/bootstrap.sh | bash
```

Then open a new shell or run:

```bash
source ~/.zshrc
codex-ts doctor
```

Use `codex-ts` for terminal automation, shell pipelines, or a drop-in command around `codex exec`:

```bash
codex-ts exec "请帮我检查这个仓库为什么测试失败"
codex-ts exec "このプロジェクトのREADMEをもっと魅力的にして"
echo "请总结这个错误日志" | codex-ts exec -
```

Inspect-first install:

```bash
git clone https://github.com/lyymuwu/TokTrans.git
cd TokTrans
./scripts/install.sh
```

Wrapper-only install:

```bash
curl -fsSL https://raw.githubusercontent.com/lyymuwu/TokTrans/main/scripts/bootstrap.sh | bash -s -- --no-skill
```

## How It Works

```text
user task
  -> translator preserves technical tokens
  -> agent-ready task in English
  -> main agent work (Codex or Claude Code)
  -> final answer translated back
```

Use TokTrans for multilingual coding, debugging, research, and ops tasks where natural-language instructions matter. Use the plain agent for short one-line chats or prompts that are mostly code, paths, and logs.

## Safety

- The official `codex` and `claude` binaries are never patched or replaced.
- `codex-ts` is a separate wrapper command (Codex only).
- The Codex `$token-trans` skill uses `fork_context: false` for translator subagents.
- The Claude Code `$token-trans` skill spawns fresh `Task` subagents on `model: haiku` with no inherited context.
- Translation prompts preserve code blocks, inline code, commands, paths, API names, filenames, JSON/YAML/TOML, stack traces, and quoted literals.
- Translator subagents must not receive repository history, files, credentials, API keys, or unrelated context.
- If translation fails, the wrapper falls back to raw Codex and the skill continues without TokTrans.

## Configuration

Configuration applies to the optional Codex CLI wrapper (`codex-ts`). The Codex skill (`~/.codex/skills/token-trans/SKILL.md`) and the Claude Code skill (`~/.claude/skills/token-trans/SKILL.md`) are stateless markdown files and have no separate config.

Default wrapper config:

```text
~/.toktrans/config.toml
```

<details>
<summary>Default values</summary>

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

</details>

`provider = "codex_cli"` reuses your Codex account and quota. To use an OpenAI-compatible endpoint:

```toml
provider = "openai"
model = "gpt-5-nano"
base_url = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"
```

## Verify

For the Codex CLI wrapper and Codex skill:

```bash
codex-ts doctor
python3 -m unittest discover -s tests
```

For the Claude Code skill:

```bash
test -f ~/.claude/skills/token-trans/SKILL.md && echo "Claude Code skill: installed"
```

Inside Claude Code, type `$token-trans hello` (or your non-English equivalent) to confirm the skill activates and the protocol runs.

Visible-token estimates are heuristic and shown only as debugging information for wrapper runs.

## Uninstall

Codex skill and `codex-ts` wrapper:

```bash
~/.toktrans/scripts/uninstall.sh --dry-run
~/.toktrans/scripts/uninstall.sh
~/.toktrans/scripts/uninstall.sh --purge --yes
```

The uninstaller removes only manifest-managed files. It preserves config and logs unless `--purge --yes` is used.

Claude Code skill:

```bash
rm -rf ~/.claude/skills/token-trans
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
