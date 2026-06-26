---
name: temp-email-coda
description: Temporary email via temp.coda.ink API — create inboxes, check emails, extract verification codes and links. Uses curl + python3 for JSON parsing.
version: "1.0"
author: alex
platforms: [linux]
metadata:
  hermes:
    tags: [temp-email, api, coda, disposable-email]
    category: productivity
---

# Temp Email (coda.ink)

## When to Use

When the user needs:
- A disposable email address for registrations
- To check incoming verification emails and extract confirmation links/codes
- To manage temporary inboxes programmatically

## Architecture

`temp.coda.ink` is a REST API. All endpoints require the `X-Session-Id` header (a UUID). Session persists inboxes across requests.

**Available domains** (from `GET /api/config`):
- `bb.coda.ink`
- `tt.coda.ink`
- `startup.coda.ink`

**Response format**: `{"success": true, "data": ...}` or `{"success": false, "error": "..."}`

## Workflow

### 1. Generate a session ID (one-time per conversation)

```bash
SESSION=$(python3 -c "import uuid; print(uuid.uuid4())")
echo $SESSION  # store this — use in ALL subsequent curl commands
```

### 2. Create a new email address

```bash
curl -s -X POST https://temp.coda.ink/api/address \
  -H 'Content-Type: application/json' \
  -H "X-Session-Id: $SESSION" \
  -d '{"provider":"tempmail"}'
```

Returns: `{"success": true, "data": {"address": "xxxxx@startup.coda.ink", "id": "...", ...}}`

To extract the email address:
```bash
ADDRESS=$(curl -s -X POST https://temp.coda.ink/api/address \
  -H 'Content-Type: application/json' \
  -H "X-Session-Id: $SESSION" \
  -d '{"provider":"tempmail"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['address'])")
echo "Created: $ADDRESS"
```

### 3. List all addresses

```bash
curl -s https://temp.coda.ink/api/addresses -H "X-Session-Id: $SESSION"
```

Extract all addresses:
```bash
curl -s https://temp.coda.ink/api/addresses -H "X-Session-Id: $SESSION" | \
  python3 -c "import sys,json; print('\n'.join(a['address'] for a in json.load(sys.stdin)['data']))"
```

### 4. Check inbox (poll for new emails)

```bash
curl -s "https://temp.coda.ink/api/emails/$ADDRESS" -H "X-Session-Id: $SESSION"
```

Wait for emails. Poll every 5-10 seconds until emails arrive (most verification emails arrive within 10-30 seconds).

Check if there are emails:
```bash
COUNT=$(curl -s "https://temp.coda.ink/api/emails/$ADDRESS" -H "X-Session-Id: $SESSION" | \
  python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']))")
echo "Emails: $COUNT"
```

### 5. Read a specific email

Get the email ID from the inbox response, then:

```bash
curl -s "https://temp.coda.ink/api/email/$EMAIL_ID" -H "X-Session-Id: $SESSION"
```

Extract subject, body_text, and from_address:
```bash
curl -s "https://temp.coda.ink/api/email/$EMAIL_ID" -H "X-Session-Id: $SESSION" | \
  python3 -c "
import sys, json
d = json.load(sys.stdin)['data']
print('From:', d['from_address'])
print('Subject:', d['subject'])
print('---')
print(d['body_text'])
"
```

### 6. Extract verification links and codes

**All links from email body (HTML):**
```bash
curl -s "https://temp.coda.ink/api/email/$EMAIL_ID" -H "X-Session-Id: $SESSION" | \
  python3 -c "
import sys, json, re
d = json.load(sys.stdin)['data']
html = d.get('body_html', '') or d.get('body_text', '')
links = re.findall(r'https?://[^\s<>\"\']+', html)
print('\n'.join(links))
"
```

**Verification codes (4-8 digit codes):**
```bash
curl -s "https://temp.coda.ink/api/email/$EMAIL_ID" -H "X-Session-Id: $SESSION" | \
  python3 -c "
import sys, json, re
d = json.load(sys.stdin)['data']
text = d.get('body_text', '')
codes = re.findall(r'\b\d{4,8}\b', text)
print('\n'.join(codes))
"
```

### 7. Delete an address

```bash
curl -s -X DELETE "https://temp.coda.ink/api/address/$ADDRESS" -H "X-Session-Id: $SESSION"
```

### 8. Delete an email

```bash
curl -s -X DELETE "https://temp.coda.ink/api/email/$EMAIL_ID" -H "X-Session-Id: $SESSION"
```

## Full Registration Workflow (Python script)

When the user wants to register on a site with a temp email, use this all-in-one script:

```bash
python3 << 'PYEOF'
import subprocess, json, time, re, uuid, sys

SESSION = str(uuid.uuid4())
BASE = "https://temp.coda.ink"

def api(method, path, body=None):
    args = ["curl", "-s", "-X", method, f"{BASE}{path}", "-H", f"X-Session-Id: {SESSION}"]
    if body:
        args += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    r = subprocess.run(args, capture_output=True, text=True)
    return json.loads(r.stdout)

# 1. Create address
res = api("POST", "/api/address", {"provider": "tempmail"})
if not res.get("success"):
    print(f"ERROR: {res.get('error')}")
    sys.exit(1)
address = res["data"]["address"]
address_id = res["data"]["id"]
print(f"EMAIL: {address}")
print(f"Use this email to register on the target site.")
print(f"Waiting for verification email (polling every 5s, max 120s)...")

# 2. Poll for emails
for _ in range(24):
    time.sleep(5)
    res = api("GET", f"/api/emails/{address}")
    emails = res.get("data", [])
    if emails:
        email_id = emails[0]["id"]
        break
else:
    print("TIMEOUT: No email received in 120s")
    sys.exit(1)

# 3. Get email content
res = api("GET", f"/api/email/{email_id}")
email = res["data"]
html = email.get("body_html", "") or email.get("body_text", "")

# 4. Extract links
links = re.findall(r'https?://[^\s<>"\']+', html)
print("\n--- VERIFICATION LINKS ---")
for link in links:
    print(link)

# 5. Extract codes
codes = re.findall(r'\b\d{4,8}\b', email.get("body_text", ""))
if codes:
    print("\n--- VERIFICATION CODES ---")
    for code in codes:
        print(code)

print("\n--- FULL EMAIL ---")
print(f"From: {email.get('from_address')}")
print(f"Subject: {email.get('subject')}")
print(email.get("body_text", "")[:500])
PYEOF
```

## Rules

- Always generate a fresh UUID session unless user explicitly wants to reuse an existing one
- Poll patiently — verification emails can take 10-60 seconds
- Extract BOTH links and codes — some sites use one or the other
- Report the email address to the user immediately after creation
- If polling exceeds 2 minutes with no email, report timeout and offer to create a new address
- Clean up: optionally delete the address when done (not required, addresses live for 10 years)
