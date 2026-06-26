---
name: fireworks-signup
description: Fireworks AI full auto signup: email → signup → verify → login → onboarding → card → API key. Step-by-step with verification after each step.
version: "3.0"
author: alex+eni
platforms: [linux]
metadata:
  hermes:
    tags: [fireworks, signup, automation, api-key, webbridge]
    category: productivity
---

# Fireworks AI Auto Signup v3 — Step-by-Step

## Critical Rules

1. **Password MUST NOT contain !@#$** — bash eats these in curl JSON. Use `Test1234.abc` (dot = special char)
2. **Wait 2 seconds after filling first password field** — Confirm Password field appears with delay
3. **Use UNIQUE WebBridge session per account** — cookies are shared across sessions
4. **Logout before each new signup** — navigate to `https://app.fireworks.ai/logout`
5. **Verify each step before continuing** — never run next step blindly

## Prerequisites

- WebBridge connected: `curl -s http://127.0.0.1:10086/status | python3 -c "import sys,json; print(json.load(sys.stdin)['extension_connected'])"` → `True`
- Unique session name per account (e.g. `fw-ac1`, `fw-ac2`, ...)

## Step 1: Create Temp Email (mail.tm)

```bash
python3 -c "
import subprocess, json, random, string
r = subprocess.run(['curl','-s','-m','15','https://api.mail.tm/domains'], capture_output=True, text=True)
domain = json.loads(r.stdout)['hydra:member'][0]['domain']
user = 'fw' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
addr = f'{user}@{domain}'
pw = 'Test1234.abc'
subprocess.run(['curl','-s','-m','15','-X','POST','https://api.mail.tm/accounts',
    '-H','Content-Type: application/json',
    '-d', json.dumps({'address': addr, 'password': pw})], capture_output=True)
r = subprocess.run(['curl','-s','-m','15','-X','POST','https://api.mail.tm/token',
    '-H','Content-Type: application/json',
    '-d', json.dumps({'address': addr, 'password': pw})], capture_output=True, text=True)
token = json.loads(r.stdout).get('token','')
print(f'EMAIL={addr}')
print(f'TOKEN={token}')
print(f'PASS={pw}')
"
```

**Verify**: `EMAIL=fw...@wshu.net`, `TOKEN=eyJ...`, `PASS=Test1234.abc`

## Step 2: Logout + Signup

```bash
SESS="fw-ac1"  # unique per account
EMAIL="fw...@wshu.net"  # from step 1
PASS="Test1234.abc"

# 2a. Logout (clear cookies)
curl -s -X POST http://127.0.0.1:10086/command \
  -d "{\"action\":\"navigate\",\"args\":{\"url\":\"https://app.fireworks.ai/logout\",\"newTab\":true},\"session\":\"$SESS\"}" > /dev/null
sleep 4

# 2b. Open signup
curl -s -X POST http://127.0.0.1:10086/command \
  -d "{\"action\":\"navigate\",\"args\":{\"url\":\"https://app.fireworks.ai/signup\",\"newTab\":false},\"session\":\"$SESS\"}" > /dev/null
sleep 5

# 2c. Fill email + click Next
SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
EREF=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'textbox', 'name': 'Email', 'ref': '(@e\d+)'\", str(t)); print(r[0])")
BREF=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'button', 'name': 'Next', 'ref': '(@e\d+)'\", str(t)); print(r[-1])")
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"fill\",\"args\":{\"selector\":\"$EREF\",\"value\":\"$EMAIL\"},\"session\":\"$SESS\"}" > /dev/null
sleep 0.3
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$BREF\"},\"session\":\"$SESS\"}" > /dev/null
sleep 5
```

**Verify**: Page should show "Password" and "Confirm Password" fields.

## Step 3: Password + Create Account

```bash
# 3a. Fill FIRST password field
SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
PW1=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'textbox', 'name': 'Password', 'ref': '(@e\d+)'\", str(t)); print(r[0])")
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"fill\",\"args\":{\"selector\":\"$PW1\",\"value\":\"$PASS\"},\"session\":\"$SESS\"}" > /dev/null
echo "Filled first password. Waiting 2s for Confirm Password to appear..."
sleep 2

# 3b. Fill SECOND password (Confirm Password)
SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
PW2=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'textbox', 'name': 'Confirm Password', 'ref': '(@e\d+)'\", str(t)); print(r[0])")
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"fill\",\"args\":{\"selector\":\"$PW2\",\"value\":\"$PASS\"},\"session\":\"$SESS\"}" > /dev/null
sleep 1

# 3c. Verify rules are green
BODY=$(curl -s -X POST http://127.0.0.1:10086/command -d '{"action":"evaluate","args":{"code":"document.body.innerText"},"session":"'$SESS'"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['value'])")
echo "$BODY" | grep -E "Password.*match|special character"  # should show "Passwords match." and "Password has special characters."
# If "Passwords match" is NOT shown — passwords not filled, STOP and debug

# 3d. Click Create Account
SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
CREF=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'button', 'name': 'Create Account', 'ref': '(@e\d+)'\", str(t)); print(r[-1])")
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$CREF\"},\"session\":\"$SESS\"}" > /dev/null
sleep 6
URL=$(curl -s -X POST http://127.0.0.1:10086/command -d '{"action":"evaluate","args":{"code":"window.location.href"},"session":"'$SESS'"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['value'])")
echo "URL: $URL"
```

**Verify**: URL must be `/signup/verify`. If still `/signup` — passwords not filled or isTrusted blocked. Check `Passwords match` rule.

## Step 4: Email Verification

```bash
TOKEN="eyJ..."  # from step 1

# Poll for verification email and extract confirmation link
for i in $(seq 1 12); do
  sleep 5
  
  # Get message list
  MSG_ID=$(curl -s -m 10 "https://api.mail.tm/messages" -H "Authorization: Bearer $TOKEN" | \
    python3 -c "import sys,json; msgs=json.load(sys.stdin).get('hydra:member',[]); print(msgs[0]['id'] if msgs else '')")
  
  if [ -z "$MSG_ID" ]; then
    echo "[$i] waiting for email..."
    continue
  fi
  
  # Download raw email and extract confirmation link
  CONFIRM_LINK=$(curl -s -m 10 "https://api.mail.tm/messages/$MSG_ID/download" -H "Authorization: Bearer $TOKEN" | \
    python3 -c "
import sys, re
raw = sys.stdin.read()
hrefs = re.findall(r'href=\"(https://[^\"]+)\"', raw)
for h in hrefs:
    if 'confirm' in h.lower() and 'confirmation_code' in h:
        print(h)
        break
")
  
  if [ -n "$CONFIRM_LINK" ]; then
    echo "[$i] Found: $CONFIRM_LINK"
    curl -s -X POST http://127.0.0.1:10086/command \
      -d "{\"action\":\"navigate\",\"args\":{\"url\":\"$CONFIRM_LINK\",\"newTab\":false},\"session\":\"$SESS\"}" > /dev/null
    sleep 5
    break
  fi
done
```

**Verify**: Page should show "Account Confirmed!" with "Sign In" button.

## Step 5: Login

```bash
# 5a. Click Sign In
SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
SIGNIN=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'button', 'name': 'Sign In', 'ref': '(@e\d+)'\", str(t)); print(r[0])")
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$SIGNIN\"},\"session\":\"$SESS\"}" > /dev/null
sleep 5

# 5b. Email Login link
SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
ELREF=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'link', 'name': 'Email Login', 'ref': '(@e\d+)'\", str(t)); print(r[0])")
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$ELREF\"},\"session\":\"$SESS\"}" > /dev/null
sleep 3

# 5c. Fill email + password + Next
SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
EMREF=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'textbox', 'name': 'Email', 'ref': '(@e\d+)'\", str(t)); print(r[0])")
PWREF=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'textbox', 'name': 'Password', 'ref': '(@e\d+)'\", str(t)); print(r[0])")
NREF=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'button', 'name': 'Next', 'ref': '(@e\d+)'\", str(t)); print(r[-1])")
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"fill\",\"args\":{\"selector\":\"$EMREF\",\"value\":\"$EMAIL\"},\"session\":\"$SESS\"}" > /dev/null
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"fill\",\"args\":{\"selector\":\"$PWREF\",\"value\":\"$PASS\"},\"session\":\"$SESS\"}" > /dev/null
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$NREF\"},\"session\":\"$SESS\"}" > /dev/null
sleep 6
```

**Verify**: URL should be `/onboarding`.

## Step 6: Onboarding

```bash
# 6a. Profile: First Name + Last Name + checkbox + Continue
SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
FN=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'textbox', 'name': 'First Name', 'ref': '(@e\d+)'\", str(t)); print(r[0])")
LN=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'textbox', 'name': 'Last Name', 'ref': '(@e\d+)'\", str(t)); print(r[0])")
CB=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'checkbox'[^}]*'ref': '(@e\d+)'\", str(t)); print(r[0])")
CN=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'button', 'name': 'Continue', 'ref': '(@e\d+)'\", str(t)); print(r[0])")
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"fill\",\"args\":{\"selector\":\"$FN\",\"value\":\"Alex\"},\"session\":\"$SESS\"}" > /dev/null
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"fill\",\"args\":{\"selector\":\"$LN\",\"value\":\"Fire\"},\"session\":\"$SESS\"}" > /dev/null
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$CB\"},\"session\":\"$SESS\"}" > /dev/null
sleep 0.5
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$CN\"},\"session\":\"$SESS\"}" > /dev/null
sleep 4

# 6b. Survey: pick Prototype (Q1) + Code Assistance (Q2) + Submit
SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
# Select checkboxes
Q1REF=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'checkbox'[^}]*'name': '[^']*Prototype[^']*'[^}]*'ref': '(@e\d+)'\", str(t)); print(r[0])")
Q2REF=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'checkbox'[^}]*'name': '[^']*Code Assistance[^']*'[^}]*'ref': '(@e\d+)'\", str(t)); print(r[0])")
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$Q1REF\"},\"session\":\"$SESS\"}" > /dev/null
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$Q2REF\"},\"session\":\"$SESS\"}" > /dev/null
sleep 0.5

SUBMIT=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'button', 'name': '[^']*Submit[^']*'[^}]*'ref': '(@e\d+)'\", str(t)); print(r[0])")
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$SUBMIT\"},\"session\":\"$SESS\"}" > /dev/null
sleep 5

# 6c. Navigate to home (Submit doesn't redirect but onboarding is complete)
curl -s -X POST http://127.0.0.1:10086/command \
  -d "{\"action\":\"navigate\",\"args\":{\"url\":\"https://app.fireworks.ai/account/home\",\"newTab\":false},\"session\":\"$SESS\"}" > /dev/null
sleep 4
URL=$(curl -s -X POST http://127.0.0.1:10086/command -d '{"action":"evaluate","args":{"code":"window.location.href"},"session":"'$SESS'"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['value'])")
echo "URL: $URL"
```

**Verify**: URL must be `/account/home` (NOT onboarding, NOT login).

## Step 7: Add Payment Card

```bash
CARD_N="6258142861861827"  # or generate via Luhn with BIN 623358637
CARD_M="01"; CARD_Y="28"; CARD_C="774"  # MM/YY/CVC

# 7a. Navigate to billing + click Add payment method
curl -s -X POST http://127.0.0.1:10086/command \
  -d "{\"action\":\"navigate\",\"args\":{\"url\":\"https://app.fireworks.ai/account/billing\",\"newTab\":false},\"session\":\"$SESS\"}" > /dev/null
sleep 4

SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
ADDREF=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'button', 'name': 'Add payment method', 'ref': '(@e\d+)'\", str(t)); print(r[0])")
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$ADDREF\"},\"session\":\"$SESS\"}" > /dev/null
sleep 5

# 7b. Click radio "Карта" to expand card fields
SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
RADIO=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'radio', 'name': 'Карта', 'ref': '(@e\d+)'\", str(t)); print(r[0] if r else 'NF')")
echo "Radio Карта: $RADIO"
if [ "$RADIO" != "NF" ]; then
  curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$RADIO\"},\"session\":\"$SESS\"}" > /dev/null
  sleep 4
fi

# 7c. Verify fields appeared
SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
HAS_CARD=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; print(len(re.findall(r'Номер карты', str(t))))")
echo "Card fields: $HAS_CARD"

if [ "$HAS_CARD" -gt 0 ]; then
  # 7d. Fill all card fields
  T=$(echo "$SNAP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['tree'])")
  python3 -c "
import subprocess, json, re
SNAP='''$T'''
for pat, val in [('Номер карты', '$CARD_N'), ('Срок', '$CARD_M/$CARD_Y'), ('CVV', '$CARD_C'),
                  ('Имя влад', 'Alex Test'), ('Адрес.*строка 1', '123 Main St'), ('Почтовый', '10001'), ('Город', 'New York')]:
    refs = re.findall(rf\"'textbox', 'name': '[^']*{pat}[^']*', 'ref': '(@e\d+)'\", SNAP)
    if refs:
        subprocess.run(['curl','-s','-X','POST','http://127.0.0.1:10086/command',
            '-H','Content-Type: application/json',
            '-d', json.dumps({'action':'fill','args':{'selector':refs[0],'value':val},'session':'$SESS'})], capture_output=True)
        print(f'Filled {pat}')
  "
  
  # 7e. Click Save
  sleep 0.5
  SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
  SAVEREF=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'button', 'name': 'Сохранить', 'ref': '(@e\d+)'\", str(t)); print(r[0])")
  curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$SAVEREF\"},\"session\":\"$SESS\"}" > /dev/null
  echo "Card submitted. Waiting redirect..."
  
  for i in $(seq 1 10); do
    sleep 4
    URL=$(curl -s -X POST http://127.0.0.1:10086/command -d '{"action":"evaluate","args":{"code":"window.location.href"},"session":"'$SESS'"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['value'])")
    echo "$URL" | grep -q fireworks && echo "$URL" | grep -qv stripe && break
  done
else
  echo "WARNING: Stripe Elements mode (iframe) — card fields not visible to WebBridge"
  echo "Try again or use Stripe API to create payment method directly"
fi
```

**Verify**: After Stripe redirect, billing page should NOT show "Add payment method" (card is attached).

**NOTE**: If fields don't expand — Stripe is in Elements mode. Use Stripe API bypass:
```bash
# Find Stripe key on page and create payment method via API
# Then bind to Fireworks via SetupIntent (TBD)
```

## Step 8: Create API Key

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -d "{\"action\":\"navigate\",\"args\":{\"url\":\"https://app.fireworks.ai/settings/users/api-keys\",\"newTab\":false},\"session\":\"$SESS\"}" > /dev/null
sleep 5

# Open Radix dropdown (bypasses isTrusted via React onKeyDown)
curl -s -X POST http://127.0.0.1:10086/command \
  -d '{"action":"evaluate","args":{"code":"(function(){var b=document.querySelectorAll(\"button\");for(var i=0;i<b.length;i++){if(b[i].innerText.includes(\"Create API Key\")){var p=Object.keys(b[i]).find(function(k){return k.startsWith(\"__reactProps$\")});if(p&&b[i][p].onKeyDown){b[i][p].onKeyDown({key:\"Enter\",code:\"Enter\",keyCode:13,preventDefault:function(){},stopPropagation:function(){}});return \"ok\";}}}return \"fail\";})()"},"session":"'$SESS'"}' > /dev/null
sleep 1

# Click menuitem "API Key"
SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
APIREF=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'menuitem', 'name': 'API Key', 'ref': '(@e\d+)'\", str(t)); api=[ref for n,ref in r if 'Service' not in n]; print(api[0] if api else '')")
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$APIREF\"},\"session\":\"$SESS\"}" > /dev/null
sleep 2

# Fill key name
SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
NAMEREF=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'textbox'[^}]*'ref': '(@e\d+)'\", str(t)); print(r[0])")
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"fill\",\"args\":{\"selector\":\"$NAMEREF\",\"value\":\"default\"},\"session\":\"$SESS\"}" > /dev/null
sleep 0.5

# Click Generate Key
SNAP=$(curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"snapshot\",\"args\":{},\"session\":\"$SESS\"}")
GENREF=$(echo "$SNAP" | python3 -c "import sys,json,re; t=json.load(sys.stdin)['data']['tree']; r=re.findall(r\"'button', 'name': 'Generate Key', 'ref': '(@e\d+)'\", str(t)); print(r[0])")
curl -s -X POST http://127.0.0.1:10086/command -d "{\"action\":\"click\",\"args\":{\"selector\":\"$GENREF\"},\"session\":\"$SESS\"}" > /dev/null
sleep 3

# Extract key
KEY=$(curl -s -X POST http://127.0.0.1:10086/command \
  -d '{"action":"evaluate","args":{"code":"(function(){var a=document.querySelectorAll(\"*\");for(var i=0;i<a.length;i++){var t=a[i].innerText;if(t&&t.startsWith(\"fw_\")&&t.length>20)return t.slice(0,80);}return \"not found\";})()"},"session":"'$SESS'"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['value'])")
echo "API KEY: $KEY"
```

**Verify**: Must print `fw_...` (starts with fw_, 28+ characters).
