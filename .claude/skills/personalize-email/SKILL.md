---
name: personalize-email
description: Tailor an approved Kettlebird Tea email draft (drafts/<slug>/email.html + email.txt) for the audience segments in data/subscribers.csv - fills merge tags like {{first_name}}, {{name}} and {{favorite_tea}} with safe fallbacks, adds a subtle segment-specific line for new, active, vip and lapsed readers, and writes per-subscriber preview files to drafts/<slug>/previews/. Use when the user asks to personalize, segment, tailor, merge, or preview an email for subscribers or segments. Not for writing a new email (use write-email), QA (use review-email), or sending.
---

# Personalize a Kettlebird Tea email for each segment

This skill makes **local preview files only**. It never sends email, calls an email API, or opens a live URL. Previews exist so the team can see how each segment will read the email.

## Hard safety rule

**Only `@example.com` addresses are ever read into output, printed, or written.** Any subscriber row whose `email` is not exactly `<local>@example.com` is refused: skip it, report it by **CSV line number only**, and never echo the address. Never process a CSV other than sample data. Every URL in a preview must be `example.com`. The script enforces this; you also check it yourself (Step 5).

## Step 1 — Load and confirm the draft is approved

1. Work out the slug. If the user didn't name one and `drafts/` has more than one folder, ask.
2. Read, in full: `CLAUDE.md` (its rules win over this skill), `brand/voice-guide.md`, `brand/products.md`, `drafts/<slug>/email.html`, `drafts/<slug>/email.txt`, and `data/subscribers.csv`.
3. Check `drafts/<slug>/review.md`. Personalize only a draft whose verdict is **PASS**. If there's no review, or it says FAIL, tell the user and offer to run `review-email` first; continue only if they say so.

## Step 2 — Map the merge tags

Tags are written `{{tag}}` or `{{tag|fallback}}`. The script fills them from the CSV:

| Tag | Filled from | If empty |
|---|---|---|
| `{{first_name}}` | first word of `name` | inline fallback, else `there` |
| `{{name}}` | `name` | inline fallback, else `there` |
| `{{favorite_tea}}` | `favorite_tea` | inline fallback, else `your favorite tea` |
| `{{segment}}` | `segment` | inline fallback |
| `{{subscriber_id}}` | a fake `preview-<segment>-<csv line>` (no real ids exist) | n/a |

- Any other tag stops the run: add it to the table above and the script, or ask the user.
- `{{email}}` is deliberately not supported in copy.
- Values are HTML-escaped in the `.html` file (e.g. "Finn O'Connor").
- Every tag you write in a callout should carry an inline fallback that reads naturally, e.g. `{{favorite_tea|your usual}}`. Read the sentence once with the value and once with the fallback.

## Step 3 — Write the segment callouts

Write `drafts/<slug>/segments.json`: one short opening line per segment, inserted as its own paragraph right after the greeting in both files. Use `""` for no callout.

```json
{
  "new": "…",
  "active": "",
  "vip": "…",
  "lapsed": "…"
}
```

What each segment needs (from `CLAUDE.md`):

| Segment | Callout | Notes |
|---|---|---|
| `new` | A warm welcome touch: glad you're here | No assumption they've ordered or tasted anything yet |
| `active` | Usually none: they get the standard copy | Add one only if it's about a story, tip or new arrival |
| `vip` | Thanks, and the inside story. Early access **only if `brand/products.md` records an early-access window or date** | Without it, don't say "early", "first" or "before anyone else"; tell the user it's available once they add it |
| `lapsed` | A gentle "we've missed you", no guilt, plus what's new | Never "where have you been", "it's been ages", or anything that scolds. Only call their tea "still here" if `products.md` lists it as always in stock |

Rules for every callout:
- **1–2 sentences, under ~40 words.** Subtle: it should read as part of the letter, not a banner.
- **Brand voice:** warm, sensory, unhurried, never hypey. No banned words, no ALL CAPS, no `!` (the email already allows at most one), no urgency.
- **Facts only from `brand/products.md`.** No discounts, early access, dates, stock claims or perks that aren't written there. If the user wants one that isn't, ask, or leave a visible `[[TODO: ...]]` in `segments.json` and don't render previews until it's resolved.
- **No links, no buttons.** One email, one CTA: the callout must not add a second action ("reply to this email", "try a sample first").
- **Plain text.** No HTML in the JSON; the script escapes and wraps it.
- Keep the rest of the draft unchanged: subject, preview text, body, CTA, sign-off and footer stay exactly as approved.

## Step 4 — Render the previews

From the repo root:

```
python .claude/skills/personalize-email/scripts/personalize.py drafts/<slug>
```

Default: the first subscriber of each segment (`new`, `active`, `vip`, `lapsed`), so at least one preview per segment. `--per-segment N` renders more; `--email someone@example.com` (repeatable) renders specific rows.

It writes `drafts/<slug>/previews/<segment>-<local-part>.html` and `.txt`. Each file starts with a `PREVIEW ONLY, not for sending` note (an HTML comment / bracketed first line). The script aborts if the draft, callouts or CSV contain a non-example.com address or URL, an unknown tag, a banned word, or a link in a callout, and it reports `PASS`/`FAIL` on each output for unresolved tags, banned words, unsafe addresses, and `.txt` lines over 78 chars.

If Python isn't available, do the same by hand: copy the draft per subscriber, fill each tag per Step 2, insert the callout after the greeting in both files (wrap the `.txt` at 78 chars), and add the preview note.

## Step 5 — Check the output yourself

Don't stop at the script's PASS:

```
grep -rnoE "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+" drafts/<slug>/previews | grep -v "@example\.com"
grep -rnoE "https?://[^\"' <>)]+" drafts/<slug>/previews | grep -vE "https?://example\.com"
grep -rn "{{" drafts/<slug>/previews
```

No output from all three means clean. Then read every preview pair and confirm:

- [ ] the greeting uses the right first name, and the callout reads naturally after it
- [ ] the callout matches its segment and is identical in the `.html` and `.txt`
- [ ] `active` (or any segment with `""`) matches the approved draft apart from merge tags
- [ ] still exactly one CTA, and the footer (address, reason, unsubscribe, preferences) is intact and last

## Step 6 — Report back

Tell the user, briefly:

- the preview files written, one line per segment with the sample subscriber
- each segment's callout text
- anything you left out and why (e.g. no early-access line because `products.md` has no early-access date)
- refused rows (line numbers only) and any pre-send notes carried over from `review.md`
