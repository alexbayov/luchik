---
name: hermes-hup-workflow
description: Hermes upgrade project workflow — state, log, protocol.
version: "0.1.0"
author: alex
platforms: [linux]
metadata:
  hermes:
    tags: [hermes, hup, workflow, project-management]
    category: devops
---

# Hermes HUP Workflow

## When to Use

When working on any HUP (Hermes Upgrade Project) task.

## Steps

1. **Check backlog** — read `docs/project/backlog.md` or `memory/tasks/<latest>`
2. **Create/update task-state** — `profile/task-state/hup<NN>-<slug>.yaml`
   - `session_id`, `task_title`, `current_goal`, `status`, `last_safe_step`, `next_step`
3. **Log decisions** — append to `profile/decision-log/<date>.jsonl`
   - Fields: `ts`, `decision`, `reason`, `alternatives`, `risk`, `approved_by`, `context`
4. **Do the work** — implement, test, verify
5. **Update task-state** — mark `status: done`, update `last_safe_step`
6. **Session summary** — write `memory/tasks/<date>-<slug>.md` if non-trivial

## Rules

- Never skip decision-log for risky or irreversible actions
- Never commit secrets, logs, runtime files
- Always update task-state before and after the work
- If blocked, set `blocked_reason` and `requires_approval: true`
