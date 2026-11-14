---
name: review-email
description: Strict QA review of a Kettlebird Tea email draft in drafts/<slug>/ (email.html + email.txt) before it goes anywhere. Checks banned words, facts against brand/products.md, subject/preview/CTA/sign-off/footer, mobile HTML, example.com-only links, and plain-text parity, then reports a Pass/Fail table with line numbers. Use when the user asks to review, audit, check, proofread, QA, or sign off on an email draft or campaign. Not for writing new emails (use write-email) and never for sending.
---

# Review a Kettlebird Tea email draft

You are a strict QA editor. Your job is to find problems, not to admire the draft. A check passes only when you have **evidence** (a search result, a count, a quoted line), never because it "looks fine".

This skill reads and edits local draft files only. It never sends email, calls an email API, or opens a live URL.

## Step 0 — Find the draft and load the sources

1. Work out the slug. If the user didn't name one and `drafts/` has more than one folder, ask which.
2. Confirm `drafts/<slug>/email.html` and `drafts/<slug>/email.txt` both exist. A missing file is an automatic **FAIL**.
3. Read, in full: `CLAUDE.md` (rules win over this skill), `brand/voice-guide.md`, `brand/products.md`, and both draft files **with line numbers** (`cat -n`). You need the line numbers for the report.

## Step 1 — Run the mechanical checks (required)

From the repo root:

```
python .claude/skills/review-email/scripts/check_draft.py drafts/<slug>
```

It is stdlib-only, reads local files, and touches no network. It prints PASS / FAIL / WARN with `file:line` for:

- banned words (case-insensitive, including other forms: unlocks, elevated, leveraging…)
- ALL CAPS words (USA, OR allowed) and more than one `!`
- subject ≤ 50 chars and identical in `Subject:` and `<title>`; preview 40–90 chars and identical in `Preview:` and the hidden preheader
- exactly one CTA link (footer links excluded), same URL in both files
- footer: the **exact** address parsed from `CLAUDE.md` Hard rule 3, the reason line, unsubscribe and preferences links, in both files
- every URL, `href`, `src` and email address on `example.com` / `@example.com`
- viewport meta, a `max-width:600px` container, no element wider than 600px, no script/form/video/external CSS
- every `<img>` has `alt` and `width`; font sizes under 16px (WARN)
- plain-text lines ≤ 78 chars, no HTML/markdown in the `.txt`
- parity: visible HTML copy vs `.txt` copy, word by word, in order
- merge tags vs the columns of `data/subscribers.csv` (WARN)

**Don't trust the script blindly, and don't stop at it.** Back up the key checks with your own searches so a script bug can't hide a problem:

```
grep -niE "delv|unlock|game.?changer|elevat|revolutionar|synerg|seamless|leverag|supercharg|next.?level|must.?have|act now|limited time|miss out|best ever|guilt.?free|detox" drafts/<slug>/email.*
grep -noE "https?://[^\"' <>)]+" drafts/<slug>/email.* | grep -vE "https?://example\.com"
grep -noE "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+" drafts/<slug>/email.* | grep -v "@example\.com"
```

No output from these three means clean. If `voice-guide.md` has gained banned words that the pattern (or `BANNED` in the script) lacks, add them to both and say so in the report.

If Python isn't available, do every bullet above by hand with `grep -n`, `awk 'length>78'` and counting; the report format doesn't change.

## Step 2 — The judgment checks (you, line by line)

These can't be scripted. Quote the offending line for every issue.

### Brand voice (`brand/voice-guide.md`)
- Warm, sensory, unhurried, never hypey. Flag vague praise ("amazing flavor"), pressure or fake urgency ("only 3 left", countdowns, "before it's gone"), gushing, jargon, snobbery.
- No health, wellness or medical claims of any kind. No "organic".
- Paragraphs 1–3 sentences; body copy roughly 120–250 words; lists ≤ 5 items.
- Greeting uses `{{first_name|there}}` (a merge tag **with a fallback**).
- Number formats: `$28`, `85°C / 185°F`, `3 minutes`.

### Facts (`brand/products.md`)
Build a small table: every claim in the email → the matching cell in `products.md`. Check **each** of:
- product and tea names, spelled and capitalised exactly ("The Steep Club")
- prices, quantities and weights (`$28/month`, `3 × 50 g`, `about 20 cups`)
- origins, tasting notes, brew temperatures and times
- dates and schedules (box season, "ships at the start of each month")
- offers: any discount, free shipping or "organic" claim is a **FAIL** unless `products.md` lists it with dates

A fact that isn't in `products.md` is a FAIL even if it's probably true. Also note anything `products.md` itself marks as unconfirmed (e.g. its **Status** line); that's a pre-send WARN.

### Required elements
- **Subject:** ≤ 50 chars, sentence case, ≤ 1 emoji, specific, no spam triggers.
- **Preview:** 40–90 chars and adds something the subject doesn't say.
- **One CTA:** one button, action-verb label of 2–5 words, from the voice guide's good examples in spirit (not "Click here", "Buy now"). Secondary links, if any, are plain text.
- **Sign-off:** a short warm line plus a person or the team ("Steep slowly, — Mara & the Kettlebird team"). "Best regards, Marketing" fails.
- **Footer, last in both files:** the address *exactly* as in `CLAUDE.md`, the reason they're receiving it, unsubscribe link, preferences link. If `CLAUDE.md` still marks the address as a sample, add a pre-send WARN.

### Technical & safety (confirm the script's findings by reading)
- Single column, table-based, inner table `width="600"` + `max-width:600px;width:100%`.
- Inline styles; `<style>` only for a mobile `@media` tweak.
- CTA is a bulletproof button (link in a table cell, not an image), ≥ 44px tall (padding top + bottom + line-height).
- Text/background contrast ≥ 4.5:1 for body, CTA and footer colours.
- No real domains, real customer addresses, tracking pixels, or API keys anywhere.

### Plain-text parity
Same copy, same order as the HTML. Links written out in full next to their label. No line over 78 chars, wrapped at word boundaries (no broken words, URLs on their own line if they'd overflow).

## Step 3 — Report

Print this table in the terminal, **and** save it to `drafts/<slug>/review.md` (overwrite any older review) so it's tracked with the draft.

```markdown
# QA review: <slug>

Reviewed <YYYY-MM-DD> · files: email.html, email.txt · verdict: **PASS** | **FAIL** (<n> fail, <n> warn)

| # | Check | Result | Evidence / issue (file:line) |
|---|---|---|---|
| 1 | Banned words | ✅ PASS | 0 hits (case-insensitive grep, both files) |
| 2 | Fact check | ❌ FAIL | email.txt:24 says "25 cups"; products.md says "about 20 cups" |
| … | | | |

## Fact table
| Claim in email | Source in products.md | Match |

## Pre-send notes
(WARNs that don't block the draft but must be resolved before a real send)

## Fixes applied
(only if the user asked for fixes: what changed, file:line, before → after)
```

Rules for the table:
- One row per check in Steps 1–2 (at least: files, banned words, caps/`!`, voice, facts, subject, preview, CTA, sign-off, footer ×2, links, mobile HTML, images/alt, contrast, plain-text format, parity, merge tags).
- **Every FAIL and WARN cites `file:line`** and quotes the text. No line number, no finding.
- Verdict is FAIL if any row fails. WARNs alone give a PASS with notes.

## Step 4 — Fix (only when asked)

If the user asked you to fix issues (or to "review and fix"):

1. Fix each FAIL in **both** files so parity holds. Use only facts from `products.md` and the address from `CLAUDE.md`. If the fix needs a fact that isn't there, don't guess: leave a visible `[[TODO: ...]]` and ask.
2. Keep the voice: rewrite the flagged phrase, don't just delete it and leave a broken sentence.
3. Re-run Step 1 and re-read the changed lines. Repeat until no FAIL remains.
4. Update `review.md` with the final table and a **Fixes applied** section (before → after, file:line).

Don't "fix" WARNs that are decisions for the user (sample address, unconfirmed product data, merge-tag naming); list them under Pre-send notes instead.

If the user only asked for a review, report and stop; offer the fixes in one line.
