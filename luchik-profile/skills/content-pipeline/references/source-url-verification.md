# Source URL Verification Guide

## The Problem

You need to cite a research source in published content. The user gave you a URL (or you found one via web_search). **Never trust a URL is working until you check it.** Plausible-looking fabricated URLs destroy credibility.

## Verification Flow

### Step 1 — Quick HEAD check

Use `curl -sI -L -A "Mozilla/5.0" -m 10 <URL>` and check HTTP status:

| Status | Meaning | Action |
|--------|---------|--------|
| **200** | ✅ Working | Use as-is |
| **301/302** | ✅ Redirect to live page | Use final URL (follow `-L`) |
| **202** | ⚠️ Bot challenge page (WAF, ddos-guard, CloudFront) | Try browser — likely works for humans |
| **403** | ⚠️ Blocked by WAF/bot protection | Same as 202 — try browser |
| **503** | ⚠️ Temporary unavailable | Retry later or find alternative |
| **404** | ❌ Dead link | Find alternative URL |
| **000 / timeout** | ❌ Unreachable | Check domain exists, try alternative |

### Step 2 — Distinguish bot-block from actual 404

Many legitimate sites (McKinsey, Deloitte, BCG, hh.ru, ВЦИОМ) show **202** or **403** to automated requests — these are not dead links. A human in a browser can access them. **Do not discard these as broken.**

Signs of bot-blocker (not dead):
- Returns 202 with a challenge page (JavaScript CAPTCHA)
- Returns 403 with HTML about automated queries
- curl shows `<title>Just a moment...</title>` or similar (Cloudflare)
- Response body is short (< 5KB) with no actual content

### Step 3 — Find alternatives for truly dead URLs

When a URL returns 404:

1. **Strip trailing path segments.** Try the root domain, then shorter paths: `raexpert.ru/researches/insurance/dmc/` → `raexpert.ru/researches/insurance/`
2. **Try Google search via web_search.** Query: `site:raexpert.ru ДМС 2024 исследование`
3. **For Russian research sites** (hh.ru, ВЦИОМ, Эксперт РА): check multiple article/ID numbers — they often renumber publications yearly
4. **For big consultancies** (Deloitte, PwC): their URL structures change every year. Search `site:deloitte.com "wellbeing" "mental health" 2024`
5. **Use delegate_task** to search while you work on other things — but **always verify** what the subagent returns with your own curl check.

### Step 4 — Document status for the user

Present results clearly grouped:

```
## ✅ Работают (HTTP 200)
- Gallup — https://...

## ⚠️ За бот-защитой (откроются в браузере)
- McKinsey — https://...

## ❌ Недоступны
- Deloitte (nuanced: URL structure changed) — совет: поищи в Google
```

### Tools Specifics

- **Python urllib** (`urllib.request.urlopen`): use `context=ssl._create_unverified_context()` for sites with SSL issues. Default timeout is infinite — always set `timeout=10`.
- **curl**: always use `-L` (follow redirects) and `-A` (set User-Agent). `-s` for silent, `-I` for headers-only (faster).
- **Fast batch check**: `for url in list; do curl -sI -L -A "Mozilla/5.0" -m 5 "$url" | head -1; done`

## Russian-Specific Sites

- **hh.ru**: behind ddos-guard; check via browser. Article IDs range widely — try multiple IDs near the publication year.
- **ВЦИОМ**: often returns 503; site is stable but CDN is aggressive. Retry later or use Google cache.
- **Эксперт РА**: URL structure changes yearly (`dmc_2024/`, `dmc_2023/`). Check by iterating years.
- **ЦБ РФ (cbr.ru)**: stable URLs but deep nesting. Strip `analytics/insurance/dmc/` to `insurance/` to find overview page.
- **СберЗдоровье**: reliable 200, no bot protection.
