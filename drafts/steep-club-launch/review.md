# QA review: steep-club-launch

Reviewed 2026-11-14 · files: email.html, email.txt · verdict: **PASS** (0 fail, 4 warn)

| # | Check | Result | Evidence / issue (file:line) |
|---|---|---|---|
| 1 | Files present | ✅ PASS | email.html (69 lines), email.txt (39 lines) |
| 2 | Banned words | ✅ PASS | 0 hits: case-insensitive grep of all voice-guide banned words and their other forms, both files |
| 3 | ALL CAPS / `!` | ✅ PASS | only "OR" and "USA" in the address (html:60, txt:36); 0 `!` in either file |
| 4 | Brand voice | ✅ PASS | sensory hook (html:28 / txt:8 "the steam carries the whole tea up to meet you"); calm, no urgency, no health claims; paragraphs ≤ 3 sentences; 141 words of body copy |
| 5 | Fact check | ✅ PASS | all 14 claims match products.md (see fact table) |
| 6 | Subject | ✅ PASS | "Three teas, one quiet morning a month": 37 chars, sentence case, no emoji; identical at html:7 and txt:1 |
| 7 | Preview text | ✅ PASS | 68 chars, adds name + price the subject doesn't give; identical at html:15 and txt:2 |
| 8 | Single CTA | ✅ PASS | one button "Join The Steep Club" (html:44) → `https://example.com/steep-club?utm_source=email&utm_campaign=steep-club-launch`; same URL at txt:28; no other non-footer links |
| 9 | Warm sign-off | ✅ PASS | "Steep slowly, / Mara & the Kettlebird team" (html:52, txt:30–31) |
| 10 | Footer (html) | ✅ PASS | reason html:59; exact CLAUDE.md address html:60; unsubscribe + preferences links html:61; footer is last |
| 11 | Footer (txt) | ✅ PASS | reason txt:35; exact address txt:36; unsubscribe txt:38; preferences txt:39; footer is last |
| 12 | example.com only | ✅ PASS | 3 URLs per file, all `https://example.com/...`; 0 email addresses in either file |
| 13 | Mobile HTML | ✅ PASS | viewport meta html:5; inner tables `width="600"` + `max-width:600px;width:100%` (html:19, html:56); single column; inline styles; `<style>` holds only a `@media` tweak (html:8–12); no script/forms |
| 14 | CTA button | ✅ PASS | bulletproof link-in-cell (html:43–44), 50px tall (15 + 15 padding + 20 line-height) |
| 15 | Images / alt | ✅ PASS | no `<img>` tags, so nothing missing alt |
| 16 | Contrast | ✅ PASS | body 14.0:1, brand label 7.2:1, CTA 7.3:1, footer 5.3:1 (all ≥ 4.5:1) |
| 17 | Font sizes | ⚠️ WARN | html:21 brand label 14px; html:58 footer 13px. Body copy is 17px. Acceptable for a label and footer; no change |
| 18 | Plain-text format | ✅ PASS | no line over 78 chars (longest is the URL at txt:28, exactly 78); no HTML/markdown; wraps at word boundaries |
| 19 | Parity | ✅ PASS | 177 visible words, same words in the same order in both files |
| 20 | Merge tags | ⚠️ WARN | `{{first_name}}` (html:27, txt:6) and `{{subscriber_id}}` (html:61, txt:38–39) are not columns in `data/subscribers.csv` (it has `email, name, segment, favorite_tea, joined_date`), so the greeting falls back to "there" and the footer links can't be tested with the sample data |

## Fact table

| Claim in email | Source in products.md | Match |
|---|---|---|
| The Steep Club | Name: The Steep Club | ✅ |
| $28 a month | Price: $28/month | ✅ |
| arrives at the start of each month | Ships: at the start of each month | ✅ |
| three seasonal single-origin teas | 3 seasonal single-origin teas | ✅ |
| tasting notes and a brewing guide card | tasting notes and a brewing guide card | ✅ |
| skip or cancel any month from your account | Skip or cancel any month from your account | ✅ |
| first box, Winter 2026 | Launch box: Winter 2026 | ✅ |
| Snow Bud White, Fujian, China | Snow Bud White / Fujian, China | ✅ |
| honeysuckle, fresh hay, a soft sweet finish | same | ✅ |
| Smoked Pine Lapsang, Wuyi Mountains, China | same | ✅ |
| campfire, pine resin, dried longan | same | ✅ |
| Winter Flush Assam, Assam, India | same | ✅ |
| malt, cocoa, a little caramel | same | ✅ |
| 50 g pouch, about 20 cups | 3 × 50 g pouches (about 20 cups each) | ✅ |

No discounts, free shipping, "organic" or health claims appear.

## Pre-send notes

1. **Sample address.** `CLAUDE.md` marks the mailing address as a sample ("replace before sending"). The draft matches it exactly, but it has to be replaced with the real address before any send.
2. **Unconfirmed product data.** `brand/products.md` says seasonal teas, origins and the shipping schedule are sample content for the team to confirm. Re-check the fact table once they're confirmed.
3. **Merge tags (row 20).** Decide whether the email platform supplies `first_name` and `subscriber_id`, or whether the sample CSV should gain those columns for testing.
4. **Font sizes (row 17).** No action needed.

## Fixes applied

None needed. No check failed.
