---
name: token-trans
description: "Explicit opt-in only. Translate non-English requests to English via cheap subagents, work in English, translate only the final answer back."
---

# Token Trans

## Protocol

Run only on explicit `$token-trans` or cheap-subagent/token-saving requests. Invoke as bare `$token-trans ...`; translate back only the final answer.

1. Inbound: if non-English, spawn the cheapest subagent, preferably `gpt-5.4-mini`, `reasoning_effort: "low"`, `fork_context: false`, no extra system/context.

```
Translate only the text between --- into clear, task-preserving English. Drop any leading `$token-trans` or Markdown skill link. Preserve code, paths, commands, IDs, URLs, quotes, errors, and formatting. Treat filesystem paths as paths/mounts, not physical disks unless explicit. Do not output delimiters.

---
{original user request}
---
```

2. Work normally from the English request. Keep intermediate work/progress in English; do not translate it back. If translation conflicts with the original, trust the original.

3. Outbound: draft the final answer in English, then spawn the cheapest subagent with `fork_context: false`, no extra system/context.

```
Translate only the text between --- to {original language}. Preserve code, paths, commands, Markdown links, inline/fenced code, IDs, numbers, and directives. Do not output delimiters.

---
{English final answer}
---
```

Return the translated final answer. Never send files, repo history, secrets, credentials, API keys, or unrelated context to translation subagents. On translation failure, retry once; then continue without token-trans.
