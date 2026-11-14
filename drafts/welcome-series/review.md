# QA review: welcome-series

Reviewed 2026-11-14 · files: email.html, email.txt · segment: `new` · verdict: **PASS** (0 fail, 4 warn)

Independent audit. Mechanical checks: `python .claude/skills/review-email/scripts/check_draft.py drafts/welcome-series` → 17 checks, 0 FAIL, 2 WARN. The three backup greps (banned words, non-example.com URLs, non-example.com addresses) returned no output. The script's `BANNED` pattern and the grep pattern cover every banned word in `brand/voice-guide.md` (lines 61–77), so nothing was missing.

| # | Check | Result | Evidence / issue (file:line) |
|---|---|---|---|
| 1 | Files present | ✅ PASS | `drafts/welcome-series/email.html` (71 lines) and `email.txt` (42 lines) both exist |
| 2 | Banned words | ✅ PASS | Script: "0 hits in both files". The backup grep (full voice-guide list incl. next-level, must-have, guilt-free, detox) found nothing |
| 3 | ALL CAPS / `!` | ✅ PASS | Script: no caps words (only USA/OR), 0 `!` in each file. My grep for `!` only matched `<!DOCTYPE` (html:1) and the CSS `!important` (html:10), which are not copy |
| 4 | Brand voice | ✅ PASS | Warm and sensory: "Pull up a chair while the kettle starts to sing." (html:28 / txt:8); "bright and floral, with a muscatel finish like ripe apricot" (html:31 / txt:18–19). No urgency, hype, health, wellness or "organic" claims (grep for organic/health/wellness/discount/free shipping/hurry/"only N" = 0 hits). Paragraphs are 1–2 sentences. The list has 3 items. Body is 182 words (script parity count), inside 120–250. Greeting `Hi {{first_name|there}},` (html:27 / txt:6). Number formats `$18`, `85°C / 185°F`, `3 minutes` are correct |
| 5 | Fact check | ✅ PASS | Every product claim matches `products.md` (see fact table). The company description comes from `CLAUDE.md` "Who we are" |
| 6 | Product data status | ⚠️ WARN | `products.md:5` Status: "Seasonal teas, origins and the shipping schedule are sample content for the team to confirm before the first send." The email states an origin: html:31 / txt:18 "It's a first flush from Darjeeling, India" |
| 7 | Audience fit (`new`) | ✅ PASS | `CLAUDE.md` says `new` needs "A welcome; who we are; an easy first tea". Welcome: html:28 "Welcome in." Who we are: html:29 "We're Kettlebird Tea, a small loose-leaf tea company…". Easy first tea: html:31–38, First Light Darjeeling with brew steps and price. There is no Steep Club or VIP-only content and no assumption of a past order |
| 8 | Subject | ✅ PASS | txt:1 / html:7 "The kettle's on. Welcome in.": 28 chars, identical in both, sentence case, no emoji, no spam triggers |
| 9 | Preview | ✅ PASS | txt:2 / html:15 "Who we are, and a bright, floral Darjeeling to start your first pot.": 68 chars, identical. It adds the Darjeeling, which the subject doesn't mention |
| 10 | One CTA | ✅ PASS | One button, html:46 "Find your first tea" (a good example in voice-guide.md:37) → `https://example.com/teas?utm_source=email&utm_campaign=welcome-series`. The same URL is at txt:30–31. No other links outside the footer |
| 11 | CTA destination | ⚠️ WARN | html:46 / txt:31 `https://example.com/teas?...`: `products.md` only lists a draft link for The Steep Club (`products.md:17`). The `/teas` path is not in any source, so confirm the real shop URL before sending |
| 12 | Sign-off | ✅ PASS | html:54 / txt:33–34 "Steep slowly, / Mara & the Kettlebird team" (matches voice-guide.md:43) |
| 13 | Footer (email.html) | ✅ PASS | It is last, in its own table (html:58–66): reason (html:61), exact address (html:62), Unsubscribe and Manage preferences links (html:63) |
| 14 | Footer (email.txt) | ✅ PASS | It is last (txt:36–42): reason (txt:38), exact address (txt:39), Unsubscribe (txt:41), Manage preferences (txt:42) |
| 15 | Sample mailing address | ⚠️ WARN | html:62 / txt:39 "Kettlebird Tea, 14 Wren Lane, Suite 2, Portland, OR 97201, USA". This matches `CLAUDE.md` exactly, but `CLAUDE.md` marks it "*(sample address: replace before sending)*" |
| 16 | Links / addresses | ✅ PASS | Script: all URLs and addresses are on example.com. Both backup greps returned nothing. No tracking pixels, images or API keys |
| 17 | Mobile HTML | ✅ PASS | Viewport meta (html:5). Single column, table-based. Inner tables use `width="600"` + `max-width:600px;width:100%` (html:19, html:58). Styles are inline; the `<style>` block holds only a `@media` padding tweak (html:8–12). No script, form or video |
| 18 | Bulletproof CTA ≥ 44px | ✅ PASS | html:45–46: link sits in a `bgcolor="#7a4b2a"` table cell, not an image. Height is 15px + 15px padding + 20px line-height = 50px |
| 19 | Images / alt | ✅ PASS | No `<img>` elements |
| 20 | Font sizes | ✅ PASS | Body and CTA are 17px (html:26, 46, 53). The script WARNs on html:21 (14px brand label) and html:60 (13px footer). Both are the allowed exceptions, so no action is needed |
| 21 | Contrast ≥ 4.5:1 | ✅ PASS | Calculated: body #2e2a25 on #fffdf8 = 14.01:1; CTA #ffffff on #7a4b2a = 7.32:1; footer #6b6259 on #f6f1e9 = 5.31:1; brand label #7a4b2a on #fffdf8 = 7.20:1 |
| 22 | Plain-text format | ✅ PASS | Longest line is 77 chars (awk). Lines wrap at word boundaries, with no HTML or markdown. The CTA URL is on its own line (txt:31), and footer links are written out in full next to their labels (txt:41–42) |
| 23 | Parity | ✅ PASS | Script: "182 words, identical order". I also read both files line by line: same copy and same order, from the brand label through to the footer |
| 24 | Merge tags | ⚠️ WARN | `{{first_name|there}}` (html:27 / txt:6) and `{{subscriber_id}}` (html:63 / txt:41–42) are not columns in `data/subscribers.csv` (columns: email, name, segment, favorite_tea, joined_date), so they can't be tested with the sample data. `{{subscriber_id}}` has no fallback, so the unsubscribe and preferences links break if the platform doesn't supply it |

## Fact table

| Claim in email | Source | Match |
|---|---|---|
| "First Light Darjeeling" (html:31 / txt:17–18) | products.md:31 **First Light Darjeeling** | ✅ |
| "a first flush from Darjeeling, India" (html:31 / txt:18) | products.md:31 "Darjeeling, India (first flush)" | ✅ (origin is sample per Status line, row 6) |
| "bright and floral, with a muscatel finish like ripe apricot" (html:31 / txt:18–19) | products.md:31 "Bright and floral, with a muscatel finish like ripe apricot" | ✅ |
| "85°C / 185°F" (html:34 / txt:23) | products.md:31 "85°C / 185°F" | ✅ |
| "Steep for 3 minutes" (html:35 / txt:24) | products.md:31 "3 minutes" | ✅ |
| "$18 for a 50 g pouch" (html:38 / txt:27) | products.md:31 "$18 / 50 g" | ✅ |
| "Copper Hollow Oolong" described as "toasty" (html:38 / txt:27–28) | products.md:33 "Toasty, buttery, roasted nuts and honey" | ✅ |
| "Misty Ridge Sencha" described as "grassy" (html:38 / txt:27–28) | products.md:32 "Grassy, brothy, a clean sweetness" | ✅ |
| "waiting on the same shelf" (in stock) (html:38 / txt:28) | products.md:27 "Flagship loose-leaf teas (always in stock)" | ✅ |
| "a small loose-leaf tea company" (html:29 / txt:10) | CLAUDE.md "Who we are": "a small loose-leaf tea company" | ✅ (CLAUDE.md) |
| "single-origin teas from small farms and send them straight to you" (html:29 / txt:10–11) | CLAUDE.md "We source single-origin teas from small farms and sell them direct" | ✅ (CLAUDE.md) |
| Discounts / free shipping / organic / health | None in email; products.md:37–39 forbids them | ✅ none made |
| Footer address (html:62 / txt:39) | CLAUDE.md Hard rule 3 | ✅ exact (sample, row 15) |

## Pre-send notes

1. **Sample address** (html:62, txt:39): replace "14 Wren Lane, Suite 2, Portland, OR 97201, USA" with the real mailing address in both files and in `CLAUDE.md` once confirmed.
2. **Unconfirmed product data** (html:31, txt:18): `products.md:5` says origins are sample content. Have the team confirm the First Light Darjeeling origin, tasting notes, brew and $18 / 50 g price before the first send.
3. **CTA destination** (html:46, txt:31): `https://example.com/teas` isn't listed in `products.md`. Add the shop link to `products.md` and swap in the real URL at send time. The UTM parameters are fine and are not a tracking pixel.
4. **Merge tags** (html:27, html:63, txt:6, txt:41–42): confirm the email platform supplies `first_name` and `subscriber_id`. The sample CSV only has `name`. Make sure `subscriber_id` is always populated, because it has no fallback and the unsubscribe and preferences links depend on it.

## Fixes applied

None — audit only.
