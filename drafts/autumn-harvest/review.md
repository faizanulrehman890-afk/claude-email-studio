# QA review: autumn-harvest

Reviewed 2026-11-14 · brand: Kettlebird Tea (default, no brand.txt) · files: email.html, email.txt · verdict: **PASS** (0 fail, 5 warn)

verdict: **PASS**

Audited by an independent auditor against `CLAUDE.md`, `brand/voice-guide.md`, `brand/products.md`. Checker: `python .claude/skills/review-email/scripts/check_draft.py drafts/autumn-harvest` → 18 checks, 0 FAIL, 2 WARN.

| # | Check | Result | Evidence / issue (file:line) |
|---|---|---|---|
| 1 | Files present | ✅ PASS | `email.html` (68 lines) and `email.txt` (37 lines) both exist; no `brand.txt`, checker Brand profile row = "Kettlebird Tea (kettlebird-tea): brand/voice-guide.md, brand/products.md" |
| 2 | Banned words | ✅ PASS | Checker 0 hits; backup grep (house pattern, both files) no output. Script `BANNED` regex and grep pattern cover all 17 items in voice-guide.md:61–77, no gap |
| 3 | ALL CAPS / `!` | ✅ PASS | Checker: no caps words (USA, OR allowed); `!` count html 0, txt 0 (`!important` at html:10 is CSS, not copy) |
| 4 | Brand voice | ✅ PASS | Warm/sensory/unhurried: html:28 "the kettle seems to sing a little longer"; html:35 "rewards a quiet minute and a second infusion". No urgency, hype or snobbery. Grep for organic/health/wellness/discount/free shipping/"only N"/hurry: 0 copy hits. Paragraphs 1–2 sentences; list 3 items; body 184 words (checker parity count, in 120–250) |
| 5 | Greeting merge tag | ✅ PASS | html:27 / txt:6 "Hi {{first_name\|there}}," (fallback present) |
| 6 | Number formats | ✅ PASS | html:31 "$18 / 50&nbsp;g", "85°C / 185°F for 3 minutes"; same style for all three teas, match products.md:31–33 |
| 7 | Fact check | ✅ PASS (1 soft claim → WARN, see Pre-send notes) | All names, origins, prices, tasting notes and brew details match products.md:31–33 exactly (see fact table). No harvest dates, discounts, shipping or "organic" claims. Soft claim html:35 / txt:23 "Each pour comes out a little different" is not stated in products.md |
| 8 | Subject | ✅ PASS | txt:1 "Three teas for the autumn kettle" = html:7 `<title>`; 32 chars, sentence case, no emoji, specific |
| 9 | Preview | ✅ PASS | txt:2 = html:15 hidden preheader "A bright Darjeeling, a brothy sencha and a toasty oolong to share." 66 chars; adds the three teas the subject doesn't name |
| 10 | One CTA | ✅ PASS | Single button html:43 "Find your autumn tea" → `https://example.com` (as per brief); txt:26 "Find your autumn tea: https://example.com". 4-word action label, in spirit of "Find your first tea". Only other links are footer |
| 11 | Sign-off | ✅ PASS | html:51 / txt:28–29 "Steep slowly, / Mara & the Kettlebird team" |
| 12 | Footer (email.html) | ✅ PASS (sample address → WARN) | Last block html:55–63: reason html:58, address html:59 "Kettlebird Tea, 14 Wren Lane, Suite 2, Portland, OR 97201, USA" (exact match CLAUDE.md rule 3), unsubscribe + preferences html:60 |
| 13 | Footer (email.txt) | ✅ PASS (sample address → WARN) | Last block txt:31–37: reason txt:33, address txt:34 (exact), unsubscribe txt:36, preferences txt:37 |
| 14 | Links / addresses | ✅ PASS | Checker: all on example.com; backup greps for non-example.com URLs and non-@example.com addresses: no output. No tracking pixels, no API keys, no images |
| 15 | Mobile HTML | ✅ PASS | html:5 viewport meta; html:19 inner table `width="600"` + `max-width:600px;width:100%`; footer table html:55 same; single column; inline styles; `<style>` html:8–12 only a `@media` padding tweak; no script/form/video/external CSS |
| 16 | Images / alt | ✅ PASS | No `<img>` elements |
| 17 | Font size | ⚠️ WARN | html:21 brand label 14px; html:57 footer 13px. Body copy 17px (html:26, 50); acceptable for label/footer only |
| 18 | CTA bulletproof + size | ✅ PASS | html:42–43 `<a>` inside `bgcolor` table cell, not an image; height 15px + 15px padding + 20px line-height = 50px ≥ 44px |
| 19 | Contrast (WCAG) | ✅ PASS | Body #2e2a25 on #fffdf8 = 14.01:1; CTA #ffffff on #7a4b2a = 7.32:1; brand label #7a4b2a on #fffdf8 = 7.20:1; footer #6b6259 on #f6f1e9 = 5.31:1 (all ≥ 4.5:1, computed) |
| 20 | Plain-text format | ✅ PASS | `awk 'length>78'` no output; checker: no HTML/markdown; wraps at word boundaries; links written out in full (txt:26, 36, 37) |
| 21 | Parity | ✅ PASS | Checker: 184 words, identical order; manual read confirms same copy html:22–60 ↔ txt:4–37 |
| 22 | Merge tags vs CSV | ⚠️ WARN | `{{first_name}}` (html:27, txt:6) and `{{subscriber_id}}` (html:60, txt:36–37) are not columns in data/subscribers.csv (columns: email, name, segment, favorite_tea, joined_date) |
| 23 | Audience segment fit | ✅ PASS | Assumed `active` (CLAUDE.md: "Stories, brewing tips, new arrivals"). Draft is brewing tips for the always-in-stock teas (html:29 "with how we like to brew them"); no welcome-only or guilt framing. Segment is not recorded in the draft files, so targeting must be set at send time (see notes) |

## Fact table

| Claim in email | Source in products.md | Match |
|---|---|---|
| html:28 / txt:9 "the three teas we always keep on the shelf" | :27 "Flagship loose-leaf teas (always in stock)", 3 rows | ✅ |
| html:31 / txt:14 "First Light Darjeeling, Darjeeling, India (first flush)" | :31 name, origin "Darjeeling, India (first flush)" | ✅ |
| html:31 / txt:14–15 "Bright and floral, with a muscatel finish like ripe apricot" | :31 tasting notes, verbatim | ✅ |
| html:31 / txt:15 "$18 / 50 g" | :31 "$18 / 50 g" | ✅ |
| html:31 / txt:15–16 "85°C / 185°F for 3 minutes" | :31 "85°C / 185°F · 3 minutes" | ✅ |
| html:32 / txt:17 "Misty Ridge Sencha, Shizuoka, Japan" | :32 | ✅ |
| html:32 / txt:17 "Grassy, brothy, a clean sweetness" | :32 verbatim | ✅ |
| html:32 / txt:18 "$16 / 50 g" | :32 "$16 / 50 g" | ✅ |
| html:32 / txt:18 "70°C / 158°F for 1.5 minutes" | :32 "70°C / 158°F · 1.5 minutes" | ✅ |
| html:33 / txt:19 "Copper Hollow Oolong, Nantou, Taiwan" | :33 | ✅ |
| html:33 / txt:19–20 "Toasty, buttery, roasted nuts and honey" | :33 verbatim | ✅ |
| html:33 / txt:20 "$22 / 50 g" | :33 "$22 / 50 g" | ✅ |
| html:33 / txt:20–21 "90°C / 194°F for 3 minutes, then steep it again, three times or more" | :33 "90°C / 194°F · 3 minutes (re-steeps 3+ times)" | ✅ |
| preview html:15 / txt:2 "bright Darjeeling, brothy sencha, toasty oolong" | :31 "Bright", :32 "brothy", :33 "Toasty" | ✅ |
| html:35 / txt:23 "Each pour comes out a little different" | Not stated (only "re-steeps 3+ times") | ⚠️ soft, unsourced |
| Harvest dates, discounts, shipping, "organic", health | None in email | ✅ (none claimed) |

## Pre-send notes

1. **Sample mailing address** — html:59 / txt:34 "Kettlebird Tea, 14 Wren Lane, Suite 2, Portland, OR 97201, USA" is marked in CLAUDE.md rule 3 as "sample address: replace before sending".
2. **Unconfirmed product data** — products.md:5 Status: "Seasonal teas, origins and the shipping schedule are sample content for the team to confirm before the first send." The origins at html:31–33 / txt:14–21 must be confirmed.
3. **Soft unsourced claim** — html:35 / txt:23 "Each pour comes out a little different". Not in products.md. Either confirm it with the team or reword to the sourced fact, e.g. "It re-steeps three times or more, so it rewards a quiet minute and a second infusion." (both files).
4. **Merge tags not in sample CSV** — `{{first_name|there}}` html:27 / txt:6 and `{{subscriber_id}}` html:60 / txt:36–37. CSV has `name`, not `first_name`, and no id column. Confirm the sending platform supplies both, or they can't be tested locally.
5. **Small type** — html:21 (14px brand label) and html:57 (13px footer). Fine for label/footer; no change needed unless the team wants 16px everywhere.
6. **Targeting** — segment (`active`) is the writer's assumption and isn't recorded in the draft. Set the audience to `active` at send time. The copy would also suit `lapsed`, but it isn't written as a welcome for `new`.

## Fixes applied

None — audit only.
