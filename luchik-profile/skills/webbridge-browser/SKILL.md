---
name: webbridge-browser
description: Control a real browser via Kimi WebBridge daemon (http://127.0.0.1:10086) — navigate, fill forms, click, extract data, screenshots. Works with the user's actual Chrome with their login sessions.
version: "1.0"
author: alex
platforms: [linux]
metadata:
  hermes:
    tags: [browser, automation, webbridge, web]
    category: productivity
---

# WebBridge Browser Control

## When to Use

When the user needs you to:
- Register on a website (fill forms, submit)
- Navigate pages and read content
- Click buttons, fill inputs, interact with web UIs
- Take screenshots of pages
- Extract data from pages that require authentication

## Architecture

A local daemon runs at `http://127.0.0.1:10086`. It controls the user's real Chrome browser with their cookies/sessions via an extension. **The extension must be installed and connected** (`extension_connected: true` in status).

Send JSON-RPC commands via curl:

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"<ACTION>","args":{...},"session":"<name>"}'
```

Use a unique `session` name per task to keep tabs isolated (e.g., `"fireworks"`, `"github"`, etc.).

## Always Check Health First

```bash
curl -s http://127.0.0.1:10086/status | python3 -c "import sys,json; s=json.load(sys.stdin); print('OK' if s.get('extension_connected') else 'EXTENSION_NOT_CONNECTED')"
```

If `EXTENSION_NOT_CONNECTED` — tell the user: "Please open Chrome with Kimi WebBridge extension active, then retry."

## Tools

### Navigate to a URL

Always use `newTab:true` on the first call for a session:

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -d '{"action":"navigate","args":{"url":"https://example.com","newTab":true},"session":"mytask"}'
```

### Read page content (Snapshot)

Returns an accessibility tree with `@e` references for interactive elements:

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -d '{"action":"snapshot","args":{},"session":"mytask"}' | python3 -c "
import sys, json
r = json.load(sys.stdin)
print(r.get('title',''))
print(r.get('url',''))
print(r.get('tree','')[:3000])
"
```

Use the `@e` refs from snapshot to click/fill elements.

### Fill an input field

Use `@e` refs from snapshot or CSS selectors. Works on `<input>`, `<textarea>`, and `[contenteditable]`:

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -d '{"action":"fill","args":{"selector":"@e42","value":"jo6wyod9@startup.coda.ink"},"session":"mytask"}'
```

For email inputs, use CSS: `input[type=email]`, `input[name=email]`, etc.

### Click an element

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -d '{"action":"click","args":{"selector":"@e15"},"session":"mytask"}'
```

Submit forms by clicking the submit button (there's no separate "press Enter").

### Screenshot (debug/verify)

Takes a PNG screenshot. The daemon returns a file path:

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"screenshot","args":{},"session":"mytask"}'
```

Read the returned `path` field to view the image.

### Execute JavaScript

For data extraction or complex interactions:

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -d '{"action":"evaluate","args":{"code":"document.title"},"session":"mytask"}'
```

Wrap in IIFE to avoid redeclaration errors: `(() => { const x = ...; return x; })()`

### List / Close Tabs

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -d '{"action":"list_tabs","args":{},"session":"mytask"}'

curl -s -X POST http://127.0.0.1:10086/command \
  -d '{"action":"close_session","args":{},"session":"mytask"}'
```

## Full Registration Workflow

When the user asks to register on a site using a temp email:

```
1. HEALTH CHECK → extension_connected?
2. Navigate to registration page (newTab:true)
3. Snapshot → find email input, password inputs, submit button
4. Create temp email via temp-email-coda skill → get address
5. Fill email field with temp address
6. Fill other fields (password, name, etc.)
7. Click submit
8. Poll temp email inbox for verification email
9. Extract verification link/code from email
10. Navigate to verification link (OR fill verification code on current page)
11. Done
```

### Common CSS selectors for signup forms

When snapshot doesn't clearly label elements, use these fallbacks:
- Email: `input[type="email"]`, `input[name="email"]`, `#email`
- Password: `input[type="password"]`, `input[name="password"]`, `#password`
- Name: `input[name="name"]`, `input[id*="name"]`, `#name`
- Submit: `button[type="submit"]`, `input[type="submit"]`, `button:has-text("Sign")`

If snapshot shows @e refs — prefer those over CSS.

## Rules

- Always check health (`extension_connected`) before any browser action
- Always use `newTab:true` on first navigate per session
- Always use unique session names per task
- Prefer snapshot `@e` refs over CSS selectors
- Close session when done (`close_session`)
- If a tool returns an error about extension version mismatch, tell the user to update the extension from https://kimi.com/features/webbridge
