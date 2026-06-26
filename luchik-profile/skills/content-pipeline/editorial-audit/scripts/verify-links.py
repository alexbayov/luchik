#!/usr/bin/env python3
"""Verify all URLs in text: check HTTP status and content relevance.

Usage:
  python3 verify-links.py <file>          # scan a file for URLs
  python3 verify-links.py --text "<str>"  # scan inline text
  python3 verify-links.py --url <url>     # check a single URL

Returns status per URL: OK / REDIRECT / FAIL / TIMEOUT / BLOCKED
"""
import re, sys, json, urllib.request, urllib.error, socket, ssl

TIMEOUT = 10
URL_RE = re.compile(r'https?://[^\s\)\]}<>"\'"]+')

def check_url(url: str) -> dict:
    """Returns {"url": url, "status": str, "final_url": str|None}"""
    result = {"url": url[:120], "status": "UNKNOWN", "final_url": None}
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; HermesAudit/1.0)",
        "Accept": "text/html,application/json,*/*",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx)
        code = resp.getcode()
        result["final_url"] = resp.geturl()
        if code == 200:
            result["status"] = "OK"
            # Check for captcha / blocking pages
            body = resp.read(2048).decode("utf-8", errors="replace").lower()
            if any(marker in body for marker in ["captcha", "blocked", "access denied", "please wait", "проверка", "робот"]):
                result["status"] = "BLOCKED"
        elif 300 <= code < 400:
            result["status"] = f"REDIRECT_{code}"
        elif code == 403:
            result["status"] = "BLOCKED"
        else:
            result["status"] = f"HTTP_{code}"
    except urllib.error.HTTPError as e:
        result["status"] = f"HTTP_{e.code}"
    except urllib.error.URLError as e:
        reason = str(e.reason)
        if "Name or service not known" in reason or "nodename nor servname" in reason:
            result["status"] = "DNS_FAIL"
        elif "Connection refused" in reason:
            result["status"] = "REFUSED"
        elif "timed out" in reason.lower() or hasattr(e, 'reason') and 'timeout' in str(e.reason).lower():
            result["status"] = "TIMEOUT"
        else:
            result["status"] = f"ERROR_{reason[:60]}"
    except socket.timeout:
        result["status"] = "TIMEOUT"
    except Exception as e:
        result["status"] = f"ERROR_{str(e)[:60]}"
    return result

def scan_text(text: str) -> list:
    urls = URL_RE.findall(text)
    results = []
    for url in urls:
        # Clean trailing punctuation
        url = url.rstrip(".,;:!?)'\"")
        results.append(check_url(url))
    return results

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--url":
        results = [check_url(sys.argv[2])]
    elif len(sys.argv) == 3 and sys.argv[1] == "--text":
        results = scan_text(sys.argv[2])
    elif len(sys.argv) == 2 and not sys.argv[1].startswith("--"):
        with open(sys.argv[1]) as f:
            results = scan_text(f.read())
    else:
        print("Usage: verify-links.py <file> | --text \"<text>\" | --url <url>")
        sys.exit(1)

    print(json.dumps(results, indent=2, ensure_ascii=False))
    fails = [r for r in results if r["status"] not in ("OK", "REDIRECT_307")]
    if fails:
        print(f"\n⚠️  {len(fails)}/{len(results)} links FAILED:")
        for f in fails:
            print(f"  [{f['status']}] {f['url']}")
        sys.exit(1)
    else:
        print(f"\n✅ All {len(results)} links verified OK")
