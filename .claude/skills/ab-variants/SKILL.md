---
name: ab-variants
description: Generate A/B test variants (subject lines, preview text and opening hooks) for an approved Kettlebird Tea email draft in drafts/<slug>/, and save them with a comparison table to drafts/<slug>/ab-variants.md. Use when the user asks to create A/B test variants, alternative or alternate subject lines, preview-text options, split-test options, or test ideas for a campaign or email. Not for writing a new email (use write-email), QA (use review-email), personalization (use personalize-email), or sending.
---

# A/B variants for a Kettlebird Tea email

This skill writes **one file of test ideas**: `drafts/<slug>/ab-variants.md`. It never edits `email.html` or `email.txt`, never sends email, and never sets up a test in an email provider.

## Step 1 — Load the sources (required)

1. Work out the slug. If the user didn't name one and `drafts/` has more than one folder, ask.
2. Read, in full:
   - `CLAUDE.md`: project rules. They win over this skill if they conflict.
   - `brand/voice-guide.md`: tone, sensory vocabulary, **banned words**, the ALL CAPS and `!` rules, subject/preview formatting.
   - `brand/products.md`: every fact a variant states (price, contents, dates, tea names, tasting notes) must be here (CLAUDE.md rule 5).
   - `drafts/<slug>/email.html` and `drafts/<slug>/email.txt`: the control subject, preview, greeting and first paragraph, and the one CTA.
3. **Approved drafts only.** Check `drafts/<slug>/review.md`. Continue only if its verdict is **PASS**. If it's missing or says FAIL, tell the user and offer to run `review-email` first.

## Step 2 — Understand the control

Note, from `email.txt`:

- the control **subject** and **preview** (`Subject:` / `Preview:` lines),
- the control **opening hook**: the first paragraph after the greeting,
- the **one CTA** and the email type (launch, welcome, newsletter, win-back),
- the facts the body already gives, so a variant never promises something the body doesn't deliver.

## Step 3 — Write three distinct variants

Each variant is a matched set: **subject + preview + opening hook**, written so it could replace the control's subject, preview and first paragraph without touching anything else. The greeting, body, CTA, sign-off and footer stay as they are.

| Variant | Angle | What it does | Leans on |
|---|---|---|---|
| **A** | Curiosity / Story | Opens a small question or scene the email answers. A moment, a why, a behind-the-scenes note. | A ritual moment, why we made it, where the tea comes from |
| **B** | Sensory / Tasting-note | Puts the tea in the reader's cup: aroma, taste, liquor colour, steam. | Tasting notes and origins **exactly as in `products.md`**, plus the voice guide's sensory vocabulary |
| **C** | Direct / Benefit | Says plainly what it is and why it's easy to say yes. | Real facts only: what's in the box, price, how it ships, skip/cancel terms |

The three must test **different ideas**, not the same line reworded. Subjects must differ from each other and from the control.

### Rules for every variant

- **Subject:** ≤ 50 characters, sentence case, no emoji unless there's a reason (max one), no merge tags.
- **Preview text:** 40–90 characters, adds something the subject doesn't say, no merge tags.
- **Opening hook:** 1–3 short sentences, ≤ 50 words, leads naturally into the existing second paragraph.
- **Banned words:** none of the voice guide's list, in any form (unlocks, elevated, leveraging). No health claims.
- **No ALL CAPS** words (abbreviations in an address are fine), **at most one `!`** in the whole email. Prefer zero.
- **No fake urgency:** no countdowns, "last chance", "only X left", unless it's true and in `products.md`.
- **Facts only from `products.md`.** Direct/Benefit is where invention creeps in: no discounts, free shipping, "cheapest", "best", or numbers that aren't there. If a variant needs a missing fact, leave it out.
- Any link or address is `example.com` / `@example.com` only. Variants usually need none.

## Step 4 — Save `drafts/<slug>/ab-variants.md`

Use exactly this layout. The checker script parses the `**Subject:**`, `**Preview:**` and `**Opening hook:**` bullet lines and the table under `## Comparison`, so keep those labels and column names.

```markdown
# A/B variants: <slug>

Generated <YYYY-MM-DD> from `email.txt` / `email.html` (review verdict: PASS).
Each variant replaces the subject, preview text and first paragraph only. Greeting, body, CTA, sign-off and footer are unchanged.

## Control (current draft)

- **Subject:** <control subject>
- **Preview:** <control preview>
- **Opening hook:** <control first paragraph>

## Variant A: Curiosity / Story

- **Subject:** ...
- **Preview:** ...
- **Opening hook:** ...

## Variant B: Sensory / Tasting-note

(same three bullets)

## Variant C: Direct / Benefit

(same three bullets)

## Comparison

| Variant | Angle | Subject | Subject chars | Preview chars | Best-fit segment | Hypothesis |
|---|---|---|---|---|---|---|
| Control | ... | ... | 37 | 68 | ... | ... |
| A | Curiosity / Story | ... | .. | .. | `new` | ... |
| B | Sensory / Tasting-note | ... | .. | .. | `active` | ... |
| C | Direct / Benefit | ... | .. | .. | `lapsed` | ... |

## Facts used

| Claim | Source in brand/products.md |
|---|---|

## How to run the test

<2–4 short lines: test one variant pair at a time, the success metric (open rate for subject/preview; click rate on the one CTA for the hook), and a reminder that this repo never sends; practice sends only via the email-outbox MCP tools.>
```

**Character counts** are Python `len()` of the exact string (an em dash or `°` counts as 1). Get them from the script, never by counting by eye.

**Best-fit segment** is one of `new`, `active`, `vip`, `lapsed` (from `CLAUDE.md`), and the **hypothesis** says *why*: tie the angle to what that segment needs from us. Phrase it as something to test ("We expect…"), not a result. Keep it to one or two sentences.

## Step 5 — Verify programmatically (required)

Run the checker and fix every FAIL, then run it again:

```bash
python .claude/skills/ab-variants/scripts/check_variants.py drafts/<slug>
```

It checks, per variant: subject ≤ 50 and preview 40–90 characters, banned words (read from `brand/voice-guide.md`, all word forms), ALL CAPS, `!` count (variant plus the rest of the email), merge tags, emoji, example.com-only links, hook size, distinct subjects, and that the table's character counts match the real ones. A useful first pass is to put placeholder counts of `0` in the table, run the script, and copy the real counts it reports.

The project's `guard_drafts.py` hook also scans `ab-variants.md` for banned words and non-example.com links whenever it's written.

Then check by reading, since a script can't:

- [ ] Every fact in every variant is in `brand/products.md` and listed in **Facts used**.
- [ ] Each variant reads in the voice guide's tone: warm, sensory, unhurried, never hypey.
- [ ] The three angles are really different, and each hook flows into the unchanged second paragraph.
- [ ] Every variant is honest about the one CTA; nothing promises what the body doesn't deliver.

## Step 6 — Report back

Tell the user briefly: the file path, the three subject lines with their counts, the checker's final PASS line, and anything they should decide (e.g. which pair to test first).
