#!/usr/bin/env python3
"""
Fireworks AI auto-signup v2 (2026-05).
Changes from v1:
- mail.tm fallback instead of coda.ink
- logout first if already logged in
- React controlled inputs handled via JS dispatchEvent
- Unique Account ID generation for onboarding
- mail.tm API returns plain lists, not hydra:member
"""
import subprocess, json, time, re, uuid, sys, random, string, urllib.request

# === CONFIG ===
CARD_NUMBER = "6258142861861827"
CARD_EXP_M = "01"
CARD_EXP_Y = "2028"
CARD_CVC = "774"
PASSWORD = "Test1234!@#$"
FIRST_NAME = "Alex"
LAST_NAME = "Test"
# ==============

def wb(action, args=None, session="fw-auto"):
    req = {"action": action, "args": args or {}, "session": session}
    r = subprocess.run(
        ["curl", "-s", "-m", "15", "-X", "POST", "http://127.0.0.1:10086/command",
         "-H", "Content-Type: application/json", "-d", json.dumps(req)],
        capture_output=True, text=True, timeout=20)
    try:
        return json.loads(r.stdout)
    except:
        return {"ok": False}

def mailtm_get_token():
    # Get domain list
    req = urllib.request.Request("https://api.mail.tm/domains", headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        domains = json.loads(resp.read().decode())
        domain = domains[0]["domain"] if isinstance(domains, list) else domains["hydra:member"][0]["domain"]
    addr = f"fwreg{int(time.time())}@{domain}"
    # Create account
    body = json.dumps({"address": addr, "password": PASSWORD}).encode()
    req = urllib.request.Request("https://api.mail.tm/accounts", data=body,
                                 headers={"Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        json.loads(resp.read().decode())  # ignore response
    # Get token
    body = json.dumps({"address": addr, "password": PASSWORD}).encode()
    req = urllib.request.Request("https://api.mail.tm/token", data=body,
                                 headers={"Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        tok = json.loads(resp.read().decode())
    return addr, tok["token"]

def mailtm_wait_verify(token, timeout=180):
    for attempt in range(timeout // 5):
        time.sleep(5)
        req = urllib.request.Request("https://api.mail.tm/messages",
                                     headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
        with urllib.request.urlopen(req) as resp:
            msgs = json.loads(resp.read().decode())
            if isinstance(msgs, list) and msgs:
                msg_id = msgs[0]["id"]
                req2 = urllib.request.Request(f"https://api.mail.tm/messages/{msg_id}",
                                              headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
                with urllib.request.urlopen(req2) as resp2:
                    msg = json.loads(resp2.read().decode())
                    body = msg.get("text", "")
                    if not body:
                        html = msg.get("html", [""])
                        body = html[0] if isinstance(html, list) else str(html)
                    links = re.findall(r'https?://[^\s<>"\']+', body)
                    for l in links:
                        if "confirm" in l.lower() or "verify" in l.lower():
                            return l
    return None

def js_set_input(label_substr, value):
    """Set React controlled input via JS events."""
    code = f"""
    (function(){{
        var inputs = document.querySelectorAll('input');
        for (var i = 0; i < inputs.length; i++) {{
            var el = inputs[i];
            var lbl = el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.name || el.id || '';
            if (lbl.toLowerCase().includes('{label_substr.lower()}')) {{
                el.value = '{value}';
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                return 'set ' + lbl;
            }}
        }}
        return 'not found';
    }})()
    """
    return wb("evaluate", {"code": code})

# === STEP 0: Logout if needed ===
wb("navigate", {"url": "https://app.fireworks.ai/logout", "newTab": False})
time.sleep(3)

# === STEP 1: Temp email ===
EMAIL, TOKEN = mailtm_get_token()
print(f"[1/10] Email: {EMAIL}")

# === STEP 2: Signup form ===
wb("navigate", {"url": "https://app.fireworks.ai/signup", "newTab": False})
time.sleep(4)

snap = wb("snapshot")
t = snap.get("data",{}).get("tree","")
email_refs = re.findall(r"'textbox', 'name': 'Email', 'ref': '(@e\d+)'", str(t))
if email_refs:
    wb("fill", {"selector": email_refs[0], "value": EMAIL})
    time.sleep(0.5)
next_refs = re.findall(r"'button', 'name': 'Next', 'ref': '(@e\d+)'", str(t))
if next_refs:
    wb("click", {"selector": next_refs[-1]})
    time.sleep(4)
print("[2/10] Email submitted")

# === STEP 3: Password ===
snap = wb("snapshot")
t = snap.get("data",{}).get("tree","")
pw = re.findall(r"'textbox', 'name': 'Password', 'ref': '(@e\d+)'", str(t))
cpw = re.findall(r"'textbox', 'name': 'Confirm Password', 'ref': '(@e\d+)'", str(t))
if pw:
    wb("fill", {"selector": pw[0], "value": PASSWORD})
if cpw:
    wb("fill", {"selector": cpw[0], "value": PASSWORD})
time.sleep(1)
btns = re.findall(r"'button', 'name': 'Create Account', 'ref': '(@e\d+)'", str(t))
if btns:
    wb("click", {"selector": btns[-1]})
    time.sleep(6)
print("[3/10] Account created")

# === STEP 4: Verify email ===
confirm_link = mailtm_wait_verify(TOKEN)
if not confirm_link:
    print("ERROR: No verification email")
    sys.exit(1)
wb("navigate", {"url": confirm_link, "newTab": False})
time.sleep(5)
print("[4/10] Email verified")

# === STEP 5: Login ===
wb("navigate", {"url": "https://app.fireworks.ai/login", "newTab": False})
time.sleep(4)
snap = wb("snapshot")
t = snap.get("data",{}).get("tree","")
email_refs = re.findall(r"'textbox', 'name': 'Email', 'ref': '(@e\d+)'", str(t))
pw_refs = re.findall(r"'textbox', 'name': 'Password', 'ref': '(@e\d+)'", str(t))
if email_refs:
    wb("fill", {"selector": email_refs[0], "value": EMAIL})
if pw_refs:
    wb("fill", {"selector": pw_refs[0], "value": PASSWORD})
next_refs = re.findall(r"'button', 'name': 'Next', 'ref': '(@e\d+)'", str(t))
if next_refs:
    wb("click", {"selector": next_refs[-1]})
    time.sleep(5)
print("[5/10] Logged in")

# === STEP 6: Onboarding ===
url = wb("evaluate", {"code": "window.location.href"}).get("data",{}).get("value","")
if "onboarding" in url:
    # Generate unique Account ID
    acc_id = "fw" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    js_set_input("account", acc_id)
    js_set_input("first name", FIRST_NAME)
    js_set_input("last name", LAST_NAME)
    time.sleep(1)
    snap = wb("snapshot")
    t = snap.get("data",{}).get("tree","")
    refs = re.findall(r"'button', 'name': 'Continue', 'ref': '(@e\d+)'", str(t))
    if refs:
        wb("click", {"selector": refs[0]})
        time.sleep(6)
    # Click Continue/Skip until we leave onboarding
    for _ in range(10):
        url = wb("evaluate", {"code": "window.location.href"}).get("data",{}).get("value","")
        if "onboarding" not in url:
            break
        snap = wb("snapshot")
        t = snap.get("data",{}).get("tree","")
        btns = re.findall(r"'button', 'name': '([^']+)', 'ref': '(@e\d+)'", str(t))
        clicked = False
        for name, ref in btns:
            if "continue" in name.lower() or "skip" in name.lower():
                wb("click", {"selector": ref})
                time.sleep(4)
                clicked = True
                break
        if not clicked:
            break
print("[6/10] Onboarding done")

# === STEP 7: Billing (optional) ===
# ... billing steps omitted for brevity, same as SKILL.md

# === STEP 8: API Keys ===
wb("navigate", {"url": "https://app.fireworks.ai/settings/users/api-keys", "newTab": False})
time.sleep(4)

# Radix dropdown bypass
open_menu_js = """(function(){var b=document.querySelectorAll('button');for(var i=0;i<b.length;i++){if(b[i].innerText.includes('Create API Key')){var p=Object.keys(b[i]).find(function(k){return k.startsWith('__reactProps$')});if(p&&b[i][p].onKeyDown){b[i][p].onKeyDown({key:'Enter',code:'Enter',keyCode:13,preventDefault:function(){},stopPropagation:function(){}});return 'ok';}}}return 'fail';})()"""
wb("evaluate", {"code": open_menu_js})
time.sleep(0.5)

snap = wb("snapshot")
t = snap.get("data",{}).get("tree","")
refs = re.findall(r"'menuitem', 'name': 'API Key', 'ref': '(@e\d+)'", str(t))
if refs:
    wb("click", {"selector": refs[0]})
time.sleep(1.5)

snap = wb("snapshot")
t = snap.get("data",{}).get("tree","")
refs = re.findall(r"'textbox'[^}]*'ref': '(@e\d+)'", str(t))
if refs:
    wb("fill", {"selector": refs[0], "value": "default-key"})
time.sleep(0.3)

snap = wb("snapshot")
t = snap.get("data",{}).get("tree","")
refs = re.findall(r"'button', 'name': 'Generate Key', 'ref': '(@e\d+)'", str(t))
if refs:
    wb("click", {"selector": refs[0]})
time.sleep(3)
print("[9/10] Key generated")

# === STEP 10: Extract ===
js_key = """(function(){var all=document.querySelectorAll('*');for(var i=0;i<all.length;i++){var t=all[i].innerText||all[i].textContent;if(t&&t.startsWith('fw_')&&t.length>20)return t.trim().split(/\s+/)[0];}return 'not found';})()"""
r = wb("evaluate", {"code": js_key})
api_key = r.get("data",{}).get("value","")
if api_key and api_key != "not found":
    print(f"\n[10/10] DONE!")
    print(f"Email:    {EMAIL}")
    print(f"API Key:  {api_key}")
else:
    print("ERROR: Could not extract API key")
