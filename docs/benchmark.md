# Translation Benchmark

This page records visible prompt-token estimates for multilingual Codex prompts before and after translation.

The numbers are intentionally conservative and reproducible: they use the same rough estimator as `codex-ts`. They are not exact billing numbers, and they do not include hidden reasoning tokens. Treat them as translation diagnostics, not product claims.

## Medium Coding Task

Task: inspect why repository tests fail and modify only the necessary files.

| Language | Task | Original visible tokens | Translated visible tokens | Delta |
|---|---|---:|---:|---:|
| Chinese | medium | 35 | 24 | -11 |
| Japanese | medium | 49 | 24 | -25 |
| Korean | medium | 41 | 24 | -17 |
| Thai | medium | 89 | 24 | -65 |
| Hindi | medium | 93 | 24 | -69 |
| Arabic | medium | 70 | 24 | -46 |
| Spanish | medium | 26 | 24 | -2 |
| French | medium | 26 | 24 | -2 |

## What This Means

Different languages and scripts can produce different visible token counts after translation. TokTrans reports those estimates as debugging context for wrapper runs, but the repository's main purpose is the translation boundary itself.

This benchmark is useful for checking how TokTrans rewrites the prompt that the main Codex run sees. It cannot inspect hidden reasoning tokens after the main model starts working.

## Reproduce

```bash
python3 scripts/benchmark_visible_tokens.py
```

For a real end-to-end check, run:

```bash
codex-ts doctor
codex-ts exec "请帮我检查这个仓库为什么测试失败，并尽量只修改必要的文件。"
```

You should see a report similar to:

```text
codex-ts: estimated prompt tokens 35 -> 24 (-11); language=Chinese; elapsed=...
```

## Benchmark Roadmap

- Add long-task prompts with refactor, tests, and explanation requests.
- Add tokenizer-specific measurements for OpenAI-compatible tokenizers.
- Add translation-quality snapshots for releases.
