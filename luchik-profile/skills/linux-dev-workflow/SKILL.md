---
name: linux-dev-workflow
description: Linux development conventions for Alex's environment.
version: "0.1.0"
author: alex
platforms: [linux]
metadata:
  hermes:
    tags: [linux, dev, bash, python]
    category: devops
---

# Linux Dev Workflow

## When to Use

When working on any software project in Alex's Linux environment (Ubuntu 26.04 LTS, x86_64).

## Environment Facts

- OS: Ubuntu 26.04 LTS, x86_64
- Shell: bash (primary), zsh (secondary)
- Python: 3.11+ available via system and venv
- Node.js: available via npm/npx
- Docker: available but not default for local dev
- Git: configured with user.name "alex"

## Bash Conventions

- Always use `set -euo pipefail` in scripts
- Quote paths with spaces using double quotes
- Prefer `workdir` parameter in bash tool over `cd && cmd`
- For JSON-in-curl: use `cat <<'EOF'` (HERE-docs) to avoid quote parsing failures
- `find`/`grep`/`cat`/`head`/`tail`/`sed`/`awk` — prefer Hermes native tools instead

## Python Conventions

- Use venv for isolated environments (not system pip)
- Prefer `pathlib.Path` over `os.path`
- Use `tmp_path` fixtures in tests, not hardcoded `/tmp`
- `get_hermes_home()` from `hermes_constants` for all HERMES_HOME paths (never hardcode `~/.hermes`)

## Project Structure

- Custom Hermes workspace: `/home/alex/hermes/` — docs, profile, memory, bin, logs
- Upstream core: `~/.hermes/hermes-agent/` — read-only, don't modify
- HumanitZ: `~/Загрузки/HumanitZ-InsaneRamZes/` — Wine launcher `~/humanitz.sh`
- Game launchers go in `~/` with `.sh` extension

## Critical Rules

1. **Never modify upstream core files** in `~/.hermes/hermes-agent/` — use plugins or workspace
2. **Git commits**: only when explicitly asked; inspect `git status`, `git diff`, `git log --oneline -10` before staging
3. **No force-push, no empty commits, no rebase** unless explicitly requested
4. **Credentials**: never log full API keys; reference variable names only
5. **Testing**: use `scripts/run_tests.sh` for Hermes tests, never `pytest` directly
