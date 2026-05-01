# Security Policy

TokTrans is intentionally a local wrapper. It does not patch the official Codex CLI package and does not overwrite the `codex` binary.

## Data Flow

When translation is enabled, user prompts that need translation are sent to the configured translation provider before the main Codex run. With the default `codex_cli` provider, this is a separate Codex CLI call configured for translation. Final `codex exec` answers are also sent to the provider for back-translation.

Do not use this wrapper with sensitive prompts unless you trust the configured provider.

## Reporting Issues

Please open a private security advisory on GitHub if available, or create an issue with minimal reproduction details and no secrets.

## Secret Handling

The repository must not include API keys, local configs, logs, `.env` files, or install manifests. The default `.gitignore` excludes those files.
