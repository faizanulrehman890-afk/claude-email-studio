# QA review: winback-tea

Reviewed 2026-11-14 · files: email.html, email.txt · verdict: **PASS** (0 fail, 5 warn)

Independent audit (review-email Steps 0–3). Script: `python .claude/skills/review-email/scripts/check_draft.py drafts/winback-tea` → "17 checks: 0 FAIL, 2 WARN". All three backup greps returned no output.

| # | Check | Result | Evidence / issue (file:line) |
|---|---|---|---|
| 1 | Files present | ✅ PASS | `drafts/winback-tea/email.html` (68 lines) and `email.txt` (39 lines) both exist |
| 2 | Banned words | ✅ PASS | Script: "0 hits in both files"; backup grep (full voice-guide list incl. next-level, must-have, guilt-free, detox): no output. Script `BANNED` regex covers every word in `voice-guide.md`; no gap |
| 3 | ALL CAPS / `!` | ✅ PASS | Script: no caps words (USA/OR allowed); 0 `!` in visible copy of either file (the only `!` characters in email.html are markup: `<!DOCTYPE` at :1 and `!important` at :10) |
| 4 | Brand voice | ✅ PASS | Warm/unhurried: email.html:28 "we hope the kettle has been kind to you"; email.html:35 "There's nothing to decide today." No urgency, no guilt, no vague praise, no health/"organic" claims (grep for organic/health/wellness/discount/free shipping/"only N": no copy hits). Paragraphs 1–2 sentences (html:28, :29, :35); list 3 items; body 163 words (txt:6–26) |
| 5 | Facts | ✅ PASS | Every name, origin, tasting note, price and brew detail matches `products.md` verbatim (see fact table). No offers, dates or discounts stated |
| 6 | Segment fit (`lapsed`) | ⚠️ WARN | Gentle hello without guilt is there (email.html:28 / email.txt:8–9), but CLAUDE.md says lapsed subscribers need "what's new" and the email only shows the existing flagships: email.html:29 "Our three flagship teas are still here on the shelf". The new Steep Club (`products.md`: "The Steep Club (monthly tea box), new") is not mentioned. Segment is inferred from the slug; the draft does not state it |
| 7 | Subject | ✅ PASS | email.txt:1 = email.html:7 "Three teas, still on the shelf for you", 38 chars, sentence case, no emoji, specific |
| 8 | Preview | ✅ PASS | email.txt:2 = email.html:15 "A bright Darjeeling, a grassy sencha, a toasty oolong. No rush." 63 chars; names the teas, which the subject doesn't |
| 9 | One CTA | ✅ PASS | email.html:43 bulletproof button "Browse our teas" (3 words, action verb) → `https://example.com/teas?utm_source=email&amp;utm_campaign=winback-tea`; email.txt:28–29 same label and URL. No other non-footer links |
| 10 | Sign-off | ✅ PASS | email.html:51 / email.txt:31–32 "Until the next pot, / The Kettlebird team" (voice-guide example) |
| 11 | Footer (email.html) | ✅ PASS | Last block, :55–63. Reason :58, address :59 exact match to CLAUDE.md Hard rule 3, Unsubscribe + Manage preferences :60 |
| 12 | Footer (email.txt) | ✅ PASS | Last block, :34–39. Reason :35, address :36 exact, Unsubscribe :38, Manage preferences :39 |
| 13 | Footer address status | ⚠️ WARN | email.html:59 / email.txt:36 "Kettlebird Tea, 14 Wren Lane, Suite 2, Portland, OR 97201, USA" — CLAUDE.md marks it "*(sample address: replace before sending)*" |
| 14 | Links & addresses | ✅ PASS | Backup URL grep and address grep: no non-example.com output. URLs: html:43, :60 (×2); txt:29, :38, :39. No email addresses in either file. No tracking pixel, no API keys |
| 15 | Mobile HTML | ✅ PASS | Viewport meta html:5; tables html:19 and :55 `width="600"` + `max-width:600px;width:100%`; single column; `<style>` (html:8–12) holds only a `@media` padding tweak; all other styles inline; no script/form/video/external CSS |
| 16 | Font sizes | ⚠️ WARN | Script WARN: email.html:21 `font-size:14px` (brand label "Kettlebird Tea") and email.html:57 `font-size:13px` (footer). Body and CTA are 17px (html:26, :43, :50). Acceptable for label/footer per script; noted only |
| 17 | Images / alt | ✅ PASS | No `<img>` elements |
| 18 | CTA size | ✅ PASS | email.html:43 padding 15px + 15px + line-height 20px = 50px ≥ 44px; link inside `<td bgcolor="#7a4b2a">` (html:42), not an image |
| 19 | Contrast | ✅ PASS | WCAG ratios computed from the hex values: body #2e2a25 on #fffdf8 = 14.01:1 (html:26/:50); CTA #ffffff on #7a4b2a = 7.32:1 (html:42–43); brand label #7a4b2a on #fffdf8 = 7.20:1 (html:21); footer text/links #6b6259 on #f6f1e9 = 5.31:1 (html:57/:60, footer table has no own background so sits on html:14/:16 #f6f1e9). All ≥ 4.5:1 |
| 20 | Plain-text format | ✅ PASS | `awk 'length>78'`: no lines; script "Plain text has no HTML/markdown: clean"; wraps at word boundaries (txt:14–23); every link written in full next to its label (txt:28–29, :38, :39) |
| 21 | Parity | ✅ PASS | Script: "192 words, identical order"; confirmed by reading html:22–60 against txt:4–39 |
| 22 | Merge tags | ⚠️ WARN | Greeting email.html:27 / email.txt:6 `{{first_name|there}}` has a fallback ✅. But `first_name` and `subscriber_id` (email.html:60, email.txt:38–39) are not columns in `data/subscribers.csv` (columns: email, name, segment, favorite_tea, joined_date), so they can't be tested with the sample data; `{{subscriber_id}}` has no fallback |
| 23 | Product data status | ⚠️ WARN | `products.md` Status line: "Seasonal teas, origins and the shipping schedule are sample content for the team to confirm before the first send." The email states origins at email.html:31–33 / email.txt:14, :18, :21 |

## Fact table

| Claim in email | Source in products.md | Match |
|---|---|---|
| "three flagship teas … still here on the shelf" (html:29, txt:11) | "Flagship loose-leaf teas (always in stock)", three rows | ✅ |
| "each from a single origin" (html:29, txt:11–12) | Each flagship has one origin; CLAUDE.md "We source single-origin teas" | ✅ |
| First Light Darjeeling (html:31, txt:14) | **First Light Darjeeling** | ✅ |
| "a first flush from Darjeeling, India" | Darjeeling, India (first flush) | ✅ (origin = sample, WARN 23) |
| "Bright and floral, with a muscatel finish like ripe apricot" | Bright and floral, with a muscatel finish like ripe apricot | ✅ |
| "$18 / 50 g" | $18 / 50 g | ✅ |
| "85°C / 185°F for 3 minutes" | 85°C / 185°F · 3 minutes | ✅ |
| Misty Ridge Sencha (html:32, txt:18) | **Misty Ridge Sencha** | ✅ |
| "from Shizuoka, Japan" | Shizuoka, Japan | ✅ (origin = sample) |
| "Grassy, brothy, a clean sweetness" | Grassy, brothy, a clean sweetness | ✅ |
| "$16 / 50 g" | $16 / 50 g | ✅ |
| "70°C / 158°F for 1.5 minutes" | 70°C / 158°F · 1.5 minutes | ✅ |
| Copper Hollow Oolong (html:33, txt:21) | **Copper Hollow Oolong** | ✅ |
| "from Nantou, Taiwan" | Nantou, Taiwan | ✅ (origin = sample) |
| "Toasty, buttery, roasted nuts and honey" | Toasty, buttery, roasted nuts and honey | ✅ |
| "$22 / 50 g" | $22 / 50 g | ✅ |
| "90°C / 194°F for 3 minutes … re-steeps 3+ times" | 90°C / 194°F · 3 minutes (re-steeps 3+ times) | ✅ |
| Preview "bright Darjeeling … grassy sencha … toasty oolong" (html:15, txt:2) | "Bright", "Grassy", "Toasty" in the tasting notes above | ✅ |
| Offers / discounts / dates | none stated | ✅ n/a |

## Pre-send notes

1. **Sample address** (email.html:59, email.txt:36): replace with the real mailing address once confirmed; CLAUDE.md marks it as a sample.
2. **Unconfirmed product data** (email.html:31–33, email.txt:14–23): `products.md` says origins are sample content to confirm before the first send.
3. **Segment fit** (email.html:29, email.txt:11): lapsed subscribers should hear "what's new". Consider one plain-text sentence (no second button) about The Steep Club using only `products.md` facts, e.g. "We've also started The Steep Club: three seasonal single-origin teas each month for $28/month, and you can skip or cancel any month." Mirror it in both files. Or confirm the flagship-only angle is intentional.
4. **Merge tags** (email.html:27, :60; email.txt:6, :38–39): confirm the sending platform supplies `first_name` and `subscriber_id` (the sample CSV only has `name`), and that an empty `subscriber_id` can't produce a broken unsubscribe link.
5. **Small type** (email.html:21 14px brand label, email.html:57 13px footer): fine for label and footer; no action needed unless you want everything ≥ 16px.

## Fixes applied

None — audit only.
