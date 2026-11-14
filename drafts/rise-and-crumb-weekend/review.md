# QA review: rise-and-crumb-weekend

Reviewed 2026-11-14 · brand: **Rise & Crumb** (`brand.txt` = `rise-and-crumb`, matches `--brand rise-and-crumb`) · files: email.html, email.txt · verdict: **PASS** (0 fail, 4 warn)

Sources: `CLAUDE.md` (hard rules), `brands/rise-and-crumb/voice-guide.md` + house banned list in `brand/voice-guide.md`, `brands/rise-and-crumb/products.md` (facts and `## Email footer`), `data/subscribers.csv` (merge tags). Checker: `python .claude/skills/review-email/scripts/check_draft.py drafts/rise-and-crumb-weekend` → 18 checks, 0 FAIL, 2 WARN.

| # | Check | Result | Evidence / issue (file:line) |
|---|---|---|---|
| 1 | Files present | ✅ PASS | `email.html` (69 lines), `email.txt` (43 lines), `brand.txt` = `rise-and-crumb` |
| 2 | Brand profile | ✅ PASS | Checker row: "Rise & Crumb (rise-and-crumb): brands/rise-and-crumb/voice-guide.md, brands/rise-and-crumb/products.md" |
| 3 | Banned words (house + Rise & Crumb) | ✅ PASS | Checker 0 hits; backup grep with the combined house + brand pattern (incl. magic, to die for, sinful, mouthwatering, superfood, clean eating, sells out fast, artisanal perfection, guilt-free, detox) → no output. Every word in both voice-guide banned lists is covered by the pattern; no gap found. |
| 4 | ALL CAPS / `!` | ✅ PASS | Only caps tokens: `NC`, `USA` (email.txt:40, address). `!` count 0 in both (only `<!DOCTYPE` and CSS `!important` in email.html:1, :10, not copy) |
| 5 | Brand voice | ✅ PASS | Warm, rustic, craft-focused: email.html:28 "their crusts crackling as they cool, and the smell of cardamom will reach the door before you do". No vague praise, no pressure or scarcity (grep for hurry/last chance/almost gone/before they/sells out: 0 hits). No health, diet, gluten-free or "organic" claims (0 hits). Paragraphs 1–3 sentences; list = 3 items (≤ 5). Body copy ≈ 189 words (email.txt:8–29), within 120–250. Number formats `$12`, `900 g`, `8 am–1 pm`, days written out. Brand name `Rise &amp; Crumb` in HTML. Note: each bullet runs to 4 short sentences/fragments (e.g. email.txt:14–16); acceptable as list items, not paragraphs. |
| 6 | Fact check | ✅ PASS | Every name, price, size, description, method, pickup day, cutoff, hours and allergen matches `products.md` (see fact table). No discounts, free items, delivery, batch limits or "organic". |
| 7 | Source data status | ⚠️ WARN | products.md:5 "**Status:** sample brand profile ... Products, prices, pickup times and the address are fictional placeholders". All facts in email.html:31–36 / email.txt:14–29 depend on it. |
| 8 | Subject | ✅ PASS | email.txt:1 / email.html:7 "What we're baking this weekend": 30 chars, identical, sentence case, no emoji, verbatim from the voice guide's good examples |
| 9 | Preview | ✅ PASS | email.txt:2 / email.html:15 "Sourdough, seeded rye, a cardamom bun. Pre-order by Thursday, 6 pm.": 67 chars, identical; adds the line-up and cutoff the subject doesn't say |
| 10 | Greeting / merge fallback | ✅ PASS | email.html:27, email.txt:6 "Hi {{first_name|there}}," |
| 11 | One CTA | ✅ PASS | Single button email.html:44 "Pre-order for the weekend" (4 words, listed as a good CTA in the voice guide) → `https://example.com/preorder?utm_source=email&utm_campaign=rc-weekend`; same URL email.txt:32 with label at :31. No other non-footer links. Note: `utm_campaign=rc-weekend` deviates from the write-email convention `utm_campaign=<slug>` (write-email SKILL.md:94); intentional (keeps email.txt:32 at 69 chars), not a failure. Base path matches products.md:32. |
| 12 | Sign-off | ✅ PASS | email.html:52 / email.txt:34–35 "See you at the counter, / Noor & the Rise & Crumb bakers" (voice guide's own example) |
| 13 | Footer (email.html) | ✅ PASS | Last block email.html:56–64: reason :59 and address :60 match products.md:49 / :48 exactly; unsubscribe + preferences links :61 with `{{subscriber_id}}` |
| 14 | Footer (email.txt) | ✅ PASS | Last block email.txt:37–43: reason :39, address :40 exact; Unsubscribe :42, Manage preferences :43 |
| 15 | Mailing address is a sample | ⚠️ WARN | email.html:60, email.txt:40 "Rise & Crumb Bakery, 88 Hearth Street, Unit 3, Asheville, NC 28801, USA"; products.md:51 "Sample address: replace before sending" |
| 16 | Links / addresses | ✅ PASS | Backup greps for non-`example.com` URLs and non-`@example.com` addresses → no output. 3 URLs per file, all `https://example.com/...` |
| 17 | Mobile HTML | ✅ PASS | Viewport meta email.html:5; table-based single column; inner tables `width="600"` + `max-width:600px;width:100%` (:19, :56); all styles inline; `<style>` (:8–12) holds only a `@media` padding tweak; no script/form/video/external CSS |
| 18 | Images / alt | ✅ PASS | No `<img>` elements, so no tracking pixels |
| 19 | Font sizes | ⚠️ WARN | email.html:21 brand label `font-size:14px`; email.html:58 footer `font-size:13px`. Both are label/footer text (permitted); body is 17px, allergen note 16px (:36). |
| 20 | Contrast | ✅ PASS | Body `#2f2924` on `#fffcf6` 14.01:1; brand label `#8a4a1f` on `#fffcf6` 6.66:1; CTA `#ffffff` on `#8a4a1f` 6.82:1; footer `#665c52` on `#f4ede3` 5.62:1 (all ≥ 4.5:1, WCAG formula) |
| 21 | Bulletproof CTA ≥ 44px | ✅ PASS | email.html:43–44 link in a `bgcolor` table cell, not an image; padding 15 + 15 + line-height 20 = 50px |
| 22 | Plain-text format | ✅ PASS | `awk 'length>78'` → no output; wrapped at word boundaries; URLs on their own lines (:32, :42, :43); no HTML/markdown (checker) |
| 23 | Parity | ✅ PASS | Checker: 238 words, identical order; manual read confirms same copy, list, allergen note, CTA, sign-off, footer order |
| 24 | Merge tags vs `data/subscribers.csv` | ⚠️ WARN | email.html:27 / email.txt:6 `{{first_name|there}}`; email.html:61, email.txt:42–43 `{{subscriber_id}}`. Neither is a CSV column (`email,name,segment,favorite_tea,joined_date`). The CSV is also Kettlebird-only sample data (`favorite_tea`), so there are no Rise & Crumb test subscribers. |
| 25 | Audience fit (active + vip) | ✅ PASS | Content is "what's on the rack" with how-it's-made detail (email.html:31–33), which fits `active` (stories, new arrivals) and the `vip` inside story. Nothing segment-wrong: no welcome copy, no "we miss you" lapsed framing. Optional: a one-line thank-you would speak more directly to `vip`. |

## Fact table

| Claim in email | Source in products.md | Match |
|---|---|---|
| "Country Sourdough", "$12", "900 g loaf" (html:31, txt:14) | :13 Country Sourdough, $12, 900 g loaf | ✅ |
| "crackly, deep-baked crust ... open, chewy crumb with a gentle tang" (html:31, txt:14–15) | :21 Crackly, deep-baked crust; open, chewy crumb; gentle tang | ✅ |
| "36-hour ferment. Hand-shaped and stone-baked" (html:31, txt:15–16) | :21 36-hour ferment, hand-shaped, stone-baked | ✅ |
| Country Sourdough "Pickup Saturday and Sunday" (html:31, txt:16) | :13 Saturday and Sunday | ✅ |
| "Seeded Rye", "$14", "800 g loaf" (html:32, txt:17) | :14 Seeded Rye, $14, 800 g loaf | ✅ |
| "dense, moist crumb, nutty and earthy ... a little caraway" (html:32, txt:17–18) | :22 Dense, moist crumb; nutty and earthy, with caraway | ✅ |
| "sunflower, flax and pumpkin seeds" (html:32, txt:18) | :14 sunflower seeds, flax seeds, pumpkin seeds | ✅ |
| "Proofed overnight and baked in a tin" (html:32, txt:18–19) | :22 Proofed overnight, baked in a tin | ✅ |
| Seeded Rye "Pickup Saturday only" (html:32, txt:19) | :14 Saturday only | ✅ |
| "Cardamom Morning Bun", "$5 each" (html:33, txt:20) | :15 Cardamom Morning Bun, $5 each | ✅ |
| "Flaky, buttery layers, laminated by hand and rolled with spiced sugar" (html:33, txt:20–21) | :23 Flaky, buttery layers; laminated by hand, rolled with spiced sugar | ✅ |
| "warm cardamom and orange zest" (html:33, txt:21) | :23 warm cardamom and orange; :15 ground cardamom, orange zest | ✅ |
| Bun "Pickup Saturday and Sunday" (html:33, txt:21–22) | :15 Saturday and Sunday | ✅ |
| "Pre-order by Thursday at 6 pm" (html:35, txt:24; preview "Thursday, 6 pm") | :9, :31 Thursday, 6 pm | ✅ |
| "waiting at the counter" (html:35, txt:24) | :29 Where: the bakery counter | ✅ |
| "Pickup is Saturday and Sunday, 8 am–1 pm" (html:35, txt:25) | :30 Saturday and Sunday, 8 am–1 pm | ✅ |
| "all three contain wheat (gluten)" (html:36, txt:27) | :36 | ✅ |
| "The Cardamom Morning Bun contains milk" (html:36, txt:27–28) | :37 | ✅ |
| "the Seeded Rye contains seeds" (html:36, txt:28) | :38 | ✅ |
| "kitchen that handles wheat, milk, eggs, seeds and tree nuts" (html:36, txt:28–29) | :39 | ✅ |
| CTA `https://example.com/preorder` (html:44, txt:32) | :32 Link (draft) | ✅ |
| Reason line (html:59, txt:39) | :49 | ✅ exact |
| Mailing address (html:60, txt:40) | :48 | ✅ exact (sample, see WARN) |

## Pre-send notes

1. **Fictional brand data** (row 7): products.md:5 marks products, prices, pickup times and address as placeholders. Confirm every fact in the fact table against the real menu before any real send.
2. **Sample mailing address** (row 15): email.html:60 / email.txt:40 use the address that products.md:51 flags "Sample address: replace before sending". Replace it in products.md first, then in both files.
3. **Merge tags** (row 24): `first_name` and `subscriber_id` aren't columns in `data/subscribers.csv`, and that CSV has no Rise & Crumb subscribers. Confirm the sending platform supplies both tags. To test locally, add a Rise & Crumb sample list with those columns.
4. **Small text** (row 19): 14px brand label (email.html:21) and 13px footer (email.html:58). These are acceptable for label and footer text. Leave them unless you want 16px throughout.
5. **UTM naming** (row 11): `utm_campaign=rc-weekend` instead of the slug, which was intentional for line length. Make sure reporting maps `rc-weekend` to `rise-and-crumb-weekend`.

## Fixes applied

None — audit only.
