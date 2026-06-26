---
name: content-pipeline
description: "Use when producing, editing, or reviewing any text content. Modular editorial pipeline with swappable role-hats (editor, writer, fact-checker, tech-writer, SEO, creative) and quality gates at each stage."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [content, editorial, pipeline, roles, quality-gates, writing]
    related_skills: [humanizer]
---

# Content Pipeline — Editorial Conveyor with Swappable Hats

## Overview

5-stage pipeline: **Brief → Draft → Review → Revise → Publish**. Roles are not baked into the agent; they are "hats" you put on via trigger words. A hat changes how the agent thinks, speaks, and checks — but the pipeline stays the same.

**Core principle:** every stage has a quality gate (QG). No gate passed = no forward movement. Fast-path exists for short notes (skip Revise, merge Draft+Review).

**Discovery Protocol:** before any work, the agent runs preflight (clarify → gather context → declare plan). If blocked — ask editor, do not improvise. Protocol state lives in `~/.hermes/protocol_state.json` and is checked by Layer 1 (systemd) through Layer 5 (watchdog).

## When to Use

- User says: "write / draft / article / post / guide / tutorial / review / rewrite / edit / fact-check / SEO / optimize / title / hook / ideate / brainstorm / check sources"
- Any content longer than a paragraph
- When user pastes a link or text and asks "what do you think?"

**Do not use for:** one-word replies, code-only requests (no prose), casual chat.

## The Pipeline

```
[BRIEF] → [DRAFT] → [REVIEW] → [REVISE] → [PUBLISH]
   QG1       QG2        QG3        QG4        QG5
```

### Stage 1 — Brief

**Input:** raw request, link, voice note, or PDF.
**Output:** structured brief (YAML frontmatter + freeform body).

Brief frontmatter fields:
- `title` — ≤ 120 chars
- `goal` — explain | persuade | instruct | compare | critique | entertain
- `audience` — who reads this
- `tone` — friendly-expert | formal | playful | urgent | neutral | snarky
- `structure` — how-to | listicle | narrative | problem-solution | comparison | storybrand | AIDA | PAS
- `word_count_min` / `word_count_max`
- `key_points` — bullet list, ≥ 2 items
- `deadline` — optional, ISO date
- `sources` — optional URLs to verify
- `primary_role` — which hat the draft stage wears (default: writer)
- `review_roles` — hats for Review stage (default: [editor, fact-checker])
- `fast_path` — true for short notes (< 500 words, trivial scope)

**QG1 (Brief Gate) — all must pass:**
1. title exists and ≤ 120 chars
2. goal is from allowed enum
3. audience is non-empty
4. key_points has ≥ 2 items
5. tone is from allowed enum
6. If sources provided, attempt HEAD check (200 = green, else warn)

### Stage 2 — Draft

**Input:** approved brief.
**Output:** raw text in markdown.

**QG2 (Draft Gate):**
1. Word count within [min, max] (if specified)
2. Exactly one H1, ≥ 2 H2 sections
3. No placeholder text: `TODO`, `[TBD]`, `lorem ipsum`
4. All links are `[text](url)` format
5. First paragraph ≠ title repetition
6. If instruct/compare: intro section is contextual (not just code/list)

### Stage 3 — Review

**Input:** draft + brief.
**Output:** annotated review (issues + suggestions). Do NOT rewrite yet.

**QG3 (Review Gate) — mandatory:**
1. Every factual claim has a source citation or `[citation needed]` marker
2. Zero AI slop (see AI Slop Patterns below)
3. Tone matches brief.tone
4. Structure matches brief.structure
5. Passive voice ≤ 30% of sentences
6. Uniqueness: if web-search available, similarity to top results < 30%

**Role-specific checks (hats applied here):**

| Hat | Trigger words | Checks |
|-----|---------------|--------|
| **fact-checker** | "фактчек", "проверь факты", "источники", "sources" | Every numeric claim verified; named entities (people, companies, versions) match reality; no hallucinated API endpoints |
| **editor** | "редактура", "edit", "proofread", "style" | Flow, transitions, hedging, repetitions, voice consistency, paragraph length variance |
| **tech-writer** | "техрайт", "гайд", "how-to", "tutorial", "guide" | Code blocks have language tags; CLI commands show expected output; no "it's simple"/"obviously"; steps are continuous |
| **SEO** | "seo", "оптимизируй", "keywords", "meta" | Primary keyword in H1; density 1-3%; H2 contain keyword variants; meta description ≤ 160 chars |
| **creative** | "идеи", "хуки", "hooks", "brainstorm", "креатив" | Hook strength, narrative arc, emotional beats, contrast, surprise factor |

### Stage 4 — Revise

**Input:** draft + review annotations.
**Output:** revised manuscript.

**QG4 (Revise Gate):**
1. All critical annotations addressed (must list resolution)
2. Revision log appended: what changed and why
3. Text diff from v1 ≤ 40% (complete rewrite = new draft, not revision)

### Stage 5 — Publish

**Input:** final manuscript.
**Output:** formatted artifact (Markdown, HTML, Telegram post, etc.).

**QG5 (Publish Gate):**
1. Formatting clean (headers, lists, code blocks, images)
2. All external links reachable (HEAD check)
3. Metadata in frontmatter (title, description, tags, author, date)
4. Preview generated if platform supports it
5. If platform is Telegram: follow Telegram-specific formatting (emoji, spoilers, short paragraphs) — see `references/telegram-webinar-announcement.md` for webinar announcement style

## Fast Path

If `fast_path: true` or user says "quick note / коротко / набросок / reply / коммент":

```
[BRIEF] → [DRAFT+REVIEW+REVISE] → [PUBLISH]
```

Merged stage uses QG2 + QG3-lite (no role-specific deep checks) + QG5.

## AI Slop Patterns (Auto-Detect)

These are forbidden in any publish-ready output. Flag during Review.

| Pattern | Example | Fix |
|---------|---------|-----|
| Hedging overload | "It's important to note that..." | Delete or state directly |
| False certainty | "This will definitely..." | Qualify or remove |
| List addiction | Every section becomes bullets | Vary: paragraph, quote, table, callout |
| Passive clustering | "It was decided that..." | Active voice |
| Boilerplate openers | "In today's fast-paced world..." | Cut. Start with story, stat, or question. |
| Boilerplate closers | "In conclusion, it is clear that..." | Cut. End with action, implication, or question. |
| Vague intensifiers | "very", "really", "quite", "extremely" | Delete or replace with concrete detail |
| Self-referential AI | "As an AI...", "I don't have feelings but..." | Never |

## Role Hats — How to Switch

User triggers a hat by keyword. The agent does NOT reload its system prompt. Instead, it applies the hat's rules to the current stage.

**Default hat (no keyword):** writer — produces clean, structured prose based on brief.

**Switching examples:**
- User: *"Фактчек этот абзац"* → agent runs fact-checker hat on that paragraph, returns annotated issues
- User: *"Перепиши как техрайтер"* → agent rewrites current text applying tech-writer hat rules
- User: *"SEO-оптимизация"* → agent reviews for SEO hat criteria and applies fixes
- User: *"Хуки для статьи"* → agent runs creative hat, generates 5 hook variants
- User: *"Редактура"* → agent runs editor hat, returns tracked changes + suggestions

**Important:** only ONE hat is active per response. If user asks for multiple hats in one message, run them sequentially (fast-path) or ask which one first.

## Example Workflow

**User:** *"Напиши статью как настроить CI/CD для Python на VPS. 1500 слов, для джунов, дружелюбный тон."*

1. **Brief:** agent outputs frontmatter + confirms structure (how-to, problem-solution)
2. **Draft:** writes 1500 words with H1/H2, code blocks, intro with hook
3. **Review:** auto-applies tech-writer + fact-checker hats (code tags, verify GitHub Actions syntax, check versions)
4. **Revise:** addresses annotations, adds revision log
5. **Publish:** outputs clean Markdown with frontmatter, code blocks tagged, links verified

**User mid-way:** *"Сделай фактчек пункта 3"* → agent switches to fact-checker hat, checks point 3, returns result. Then resumes pipeline.

**User at end:** *"SEO-оптимизация"* → agent switches to SEO hat, runs QG3-SEO checks, applies fixes, returns revised version.

## Common Pitfalls

1. **Skipping the Brief.** 60% of revision rounds come from missing brief. Always write brief first, even if it's 5 lines.
2. **Multiple hats at once.** "Проверь факты, отредактируй стиль и сделай SEO" — this is three Review passes. Do them sequentially or ask user to pick priority.
3. **Rewriting instead of revising.** If diff > 40%, it's a new Draft, not a Revise. Warn user.
4. **Not checking links.** Dead links in published content destroy credibility. Always QG5-link-check. See `references/source-url-verification.md` for the full URL verification protocol — distinguishing bot-blockers from actual 404s, finding alternatives, and handling Russian-specific research sites.
5. **Ignoring visual references.** When the user provides a screenshot or image as a reference for style/structure, do not approximate — OCR it first. See `references/image-ocr-tesseractjs.md` for OCR via tesseract.js (WASM, no native binary needed).
6. **Forgetting the audience.** A "friendly-expert" tone for CTOs is wrong. Audience drives tone, structure, and depth.

## Verification Checklist

- [ ] Brief exists with all mandatory fields (title, goal, audience, tone, key_points)
- [ ] Draft passes QG2 (structure, placeholders, word count)
- [ ] Review passes QG3 (facts cited, no slop, tone match, passive ≤ 30%)
- [ ] Revise passes QG4 (all critical issues resolved, revision log present)
- [ ] Publish passes QG5 (formatting, links, metadata)
- [ ] If role hats were requested, their specific checks are logged in review output
- [ ] Fast-path requests are flagged and merged stages are documented
