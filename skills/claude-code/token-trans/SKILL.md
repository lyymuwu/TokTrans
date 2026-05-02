---
name: token-trans
description: "Explicit opt-in only. Translate multilingual requests through lightweight Claude Code subagents, work normally in English, then translate only the final answer back. Trigger on `$token-trans` invocations or explicit TokTrans references."
---

# Token Trans (Claude Code)

## Protocol

Run only on explicit `$token-trans` or TokTrans requests. Invoke as bare `$token-trans ...`; translate back only the final answer.

1. Inbound: if non-English, spawn the cheapest Claude Code subagent. Use the `Task` tool with `subagent_type: "general-purpose"` and `model: "haiku"`. Pass NO files, repo history, secrets, or unrelated context — only the translation prompt below.

```
Translate only the text between --- into clear, task-preserving English. Drop any leading `$token-trans` or Markdown skill link. Preserve code, paths, commands, IDs, URLs, quotes, errors, and formatting. Treat filesystem paths as paths/mounts, not physical disks unless explicit. Do not output delimiters.

---
{original user request}
---
```

2. Work normally from the English request using the main Claude Code agent. Keep intermediate work, plans, tool calls, and progress notes in English; do not translate them back. If the translation appears to conflict with the original request, trust the original.

3. Outbound: draft the final answer in English. Then spawn another cheapest Claude Code subagent (`Task` with `subagent_type: "general-purpose"` and `model: "haiku"`), again with no extra context, using:

```
Translate only the text between --- to {original language}. Preserve code, paths, commands, Markdown links, inline/fenced code, IDs, numbers, and directives. Do not output delimiters.

---
{English final answer}
---
```

Return the translated final answer to the user. Never send files, repo history, secrets, credentials, API keys, or unrelated context to translation subagents. On translation failure, retry the subagent call once; then continue without token-trans (answer in English or in the original language as best-effort).
