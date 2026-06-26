---
name: debugging-protocol
description: How to debug without getting stuck in loops.
version: "0.1.0"
author: alex
platforms: [linux]
metadata:
  hermes:
    tags: [debugging, anti-carousel, troubleshooting]
    category: devops
---

# Debugging Protocol

## Anti-Carousel Rules

1. **Never read the same file 3+ times** without a write/terminal action in between
2. **Never run the same search query 3+ times** — reformulate or use the results already found
3. **Never run the same terminal command 3+ times** with identical output
4. **After 5+ read-only tools**, must do a mutating action (write, patch, test, commit) or ask user

## Debugging Steps

1. **Read logs first** — `hermes logs`, `errors.log`, session JSON
2. **Make minimal reproduce** — smallest file/command that shows the bug
3. **One change at a time** — change → test → observe
4. **If stuck 3 turns**, switch strategy or ask user

## What Counts as Progress

- File write, patch, delete
- Terminal command with new/different output
- git commit, push
- Successful test run
- New directory created
- Package installed

## Forbidden Loops

- grep → read → grep → read (same files)
- cat → cat → cat (same file, no action)
- test → fail → same test → fail (no code change)
- ask clarification → ask clarification → ask clarification (decide instead)
