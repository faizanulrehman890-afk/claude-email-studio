---
name: write-email
description: Draft Kettlebird Tea marketing emails (welcome, product launch, newsletter, win-back) as a matched HTML + plain-text pair in drafts/<slug>/. Use when the user asks to write, draft, create, or rework a marketing email, newsletter, campaign, announcement, or promo email for Kettlebird Tea. Not for transactional email code or sending.
---

# Write a Kettlebird Tea marketing email

This skill produces a **draft only**. It never sends email, calls an email API, or adds real recipient addresses.

## Step 1 — Load the brand sources (required)

Read all three before writing a word:

1. `CLAUDE.md` — project rules (these win over this skill if they conflict).
2. `brand/voice-guide.md` — tone, words we use, **banned words**, sign-off style.
3. `brand/products.md` — the only allowed source of product names, prices, contents, dates and offers.

If any file is missing, or the product the email is about isn't in `brand/products.md`, **stop and ask the user** for the missing facts. Never invent a price, ship date, discount, ingredient, or product name. If the user wants to proceed anyway, put the gap in the draft as a visible `[[TODO: ...]]` placeholder and list it in your summary.

## Step 2 — Pin down the brief

Settle these before writing, from the user's request or by asking:

- **Type:** welcome, product launch, newsletter, or win-back (see Step 3).
- **Audience:** one or more segments from `CLAUDE.md`: `new`, `active`, `vip`, `lapsed`. Natural fits: welcome → `new`, win-back → `lapsed`, launch → `active` + `vip` (vip can get an early-access line). To check merge tags, use only the fake rows in `data/subscribers.csv` (`name`, `favorite_tea`).
- **The one action:** the single thing the reader should do. One email, one CTA.
- **Slug:** short kebab-case name for the folder, e.g. `steep-club-launch`.

## Step 3 — Shape by email type

| Type | Goal | Hook angle | CTA example |
|---|---|---|---|
| **Welcome** | Make a new subscriber feel at home; set expectations | Who we are and why we started; what they'll get from us | "Find your first tea" |
| **Product launch** | Announce one new product and drive the first purchase/sign-up | The moment or problem the product solves; a sensory detail | "Join The Steep Club" |
| **Newsletter** | Keep the relationship warm; give value before asking | A seasonal story, brewing tip, or behind-the-scenes note | "Read the full brewing guide" |
| **Win-back** | Re-engage someone who's gone quiet, without guilt | "We've changed / we kept your spot", what's new since they left | "See what's new" |

Even a newsletter with several sections keeps **one** primary CTA button. Secondary items are plain text links.

## Step 4 — Write the copy in this structure

Every email has these parts, in this order:

1. **Subject line** — ≤ 50 characters, specific, no ALL CAPS, at most one emoji (only if the voice guide allows), no spam triggers ("FREE!!!", "Act now").
2. **Preview text** — 40–90 characters, adds to the subject rather than repeating it.
3. **Greeting** — warm and personal, e.g. `Hi {{first_name|there}},` (the merge tag needs a fallback).
4. **Story / hook** — 1–3 short sentences that pull the reader in.
5. **Main body** — short paragraphs (≤ 3 sentences each). Real product details from `brand/products.md`. Bullets are fine for "what's inside".
6. **Single clear CTA** — one button, action-verb label of 2–5 words.
7. **Warm sign-off** — in the voice guide's style, e.g. "Steep slowly, — Mara & the Kettlebird team".
8. **Footer (required)** — the mailing address exactly as written in `CLAUDE.md` (currently `Kettlebird Tea, 14 Wren Lane, Suite 2, Portland, OR 97201, USA`), why they're receiving this ("You're getting this because you subscribed to Kettlebird Tea emails."), an unsubscribe link, and a manage-preferences link.

Write in the voice guide's tone. Read the copy aloud in your head; cut anything that sounds like an ad template.

## Step 5 — Save the two files

Create `drafts/<slug>/` with:

- `email.html` — the HTML version.
- `email.txt` — the plain-text version, same copy and same order.

Put the subject line and preview text at the top of `email.txt` (as `Subject:` / `Preview:` lines), and in the HTML as `<title>` plus a hidden preheader `<div>`.

### HTML rules

- Full document: `<!DOCTYPE html>`, `<html lang="en">`, `<meta charset="utf-8">`, `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- **Single column**, table-based layout: an outer 100%-width table and an inner table with `width="600"` and `style="max-width:600px;width:100%"`. Nothing wider than 600px.
- **Inline styles only** on content elements. A small `<style>` block in `<head>` is allowed only for a mobile `@media` tweak. No external CSS, no web fonts that break the email without a fallback, no JavaScript, no forms, no video.
- Font stack fallback such as `Georgia, 'Times New Roman', serif` or `Helvetica, Arial, sans-serif`; body text ≥ 16px, line-height ≈ 1.5.
- CTA is a "bulletproof" button: a link styled as a button inside a table cell, not an image. At least 44px tall.
- Images: none are required. Any `<img>` needs `alt`, explicit `width`, `style="display:block;max-width:100%;height:auto"`, and a placeholder `src` on `example.com`.
- Text/background contrast at least 4.5:1.
- Hidden preheader right after `<body>`:
  `<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">Preview text here</div>`

### Plain-text rules

- No HTML or markdown syntax. Lines ≤ 78 characters.
- Write links out in full, e.g. `Join The Steep Club: https://example.com/steep-club`.
- Include the full footer, unsubscribe URL and address included.

### Link rules

- **Every URL uses `example.com`** (e.g. `https://example.com/steep-club?utm_source=email&utm_campaign=<slug>`). Never a real domain, real customer address, or a live tracking link. Real links are swapped in at send time.
- Unsubscribe: `https://example.com/unsubscribe?id={{subscriber_id}}`. Preferences: `https://example.com/preferences?id={{subscriber_id}}`.
- Any email address shown uses `@example.com` (e.g. `hello@example.com`).

## Step 6 — Self-check (all must pass before you finish)

Go through every line. Fix anything that fails and check again. Don't report done until every box is ticked.

- [ ] **Banned words:** none of the banned words or phrases from `brand/voice-guide.md` appear in either file. Search for each one (case-insensitive) in both files. Don't eyeball it. For example:
  `grep -niE "delve|unlock|game.?changer|elevat|revolutionar|synergy|seamless|leverag|supercharg|next.level|must.have|act now|limited time|miss out|best ever|guilt.free|detox" drafts/<slug>/email.*`
  Also check there are no health claims, no ALL CAPS words, and at most one `!`.
- [ ] **Voice:** tone matches the voice guide, and the sign-off follows its style.
- [ ] **Real product details:** every product name, price, quantity, date and offer matches `brand/products.md` exactly. Nothing is invented. Any gaps are visible `[[TODO]]`s and listed for the user.
- [ ] **Structure:** subject (≤ 50 chars), preview (40–90 chars), greeting, hook, body, exactly **one** CTA button, sign-off, footer, in that order.
- [ ] **Footer:** company name, physical address, reason for receiving, unsubscribe link and preferences link, in **both** files.
- [ ] **Mobile-friendly HTML:** single column, container max 600px, viewport meta, inline styles, no element with a fixed width over 600px, body text ≥ 16px, tappable CTA ≥ 44px.
- [ ] **Safe links:** every `href`, `src` and URL in either file points to `example.com`, and every email address is `@example.com`. Verify with a search for `http` and `@`.
- [ ] **Parity:** `email.txt` has the same copy, in the same order, as `email.html`.
- [ ] **HTML is well-formed:** tags balanced, no `<script>`, no external stylesheets.

## Step 7 — Report back

Tell the user, briefly:

- the folder path and both file names
- the subject line and preview text
- the CTA and where it points
- any `[[TODO]]` placeholders or assumptions they need to resolve before sending
