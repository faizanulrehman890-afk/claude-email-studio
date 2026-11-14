---
name: switch-brand
description: Draft or audit an email for a brand other than Kettlebird Tea (e.g. Rise & Crumb) using a brand profile in brands/<brand>/ as the source of truth, while every CLAUDE.md hard safety rule stays on. Use when the user mentions another brand, a --brand flag (e.g. "--brand rise-and-crumb"), "switch brand", "for Rise & Crumb", or wants to add a new brand profile. Works with write-email, review-email, campaign-writer and campaign-auditor.
---

# Switch brand

The studio's default brand is **Kettlebird Tea** (`brand/` + `CLAUDE.md`). Other brands live in `brands/<brand>/` and are selected per draft. Nothing global is switched, so Kettlebird drafts are never affected.

## What a brand profile is

```
brands/<brand>/voice-guide.md   tone, vocabulary, sign-off, "## Banned words and phrases"
brands/<brand>/products.md      products, prices, dates + an "## Email footer" table
```

The `## Email footer` table in `products.md` must have these rows (read by `scripts/brand_profile.py`):

| Field | Detail |
|---|---|
| Brand name | Rise & Crumb |
| Mailing address | `<full address, one line>` |
| Reason line | `You're getting this because ...` |

Existing profiles: `rise-and-crumb` (fictional sourdough bakery).

## How to select a brand for a draft

1. Get the brand slug from the request: `--brand rise-and-crumb`, "for Rise & Crumb", etc. If `brands/<brand>/` doesn't exist, stop and ask. Don't make a profile up mid-campaign.
2. Create `drafts/<slug>/brand.txt` containing only the brand slug (e.g. `rise-and-crumb`). This marker is what the checker, the guard hook and the pre-commit audit use. No marker means Kettlebird.
3. Run `write-email` / `review-email` (or the `campaign-writer` / `campaign-auditor` agents) with the **source substitutions** below.

## Source substitutions (brand override)

| In the Kettlebird workflow | With `--brand <brand>` use |
|---|---|
| `brand/voice-guide.md` | `brands/<brand>/voice-guide.md` **and** the banned list in `brand/voice-guide.md` (house list, still applies) |
| `brand/products.md` | `brands/<brand>/products.md` (the only source of facts) |
| Footer address from `CLAUDE.md` Hard rule 3 | `Mailing address` row in `brands/<brand>/products.md` |
| "You're getting this because you subscribed to Kettlebird Tea emails." | `Reason line` row in `brands/<brand>/products.md` |
| Kettlebird sign-off ("Steep slowly, ...") | The sign-off style in the brand's voice guide |
| Segments in `CLAUDE.md` | Same four segment names (`new`, `active`, `vip`, `lapsed`); describe them in the brand's terms |
| Tea examples in the skills (`The Steep Club`, `°C`) | Ignore; they're Kettlebird examples, not rules |

## Rules that never change, whatever the brand

These come from `CLAUDE.md` and stay active for every brand:

- Drafts only. **Never send for real.** Practice sends only through the local `email-outbox` MCP tools.
- **Only `@example.com`** email addresses and **only `example.com`** links.
- **One email, one CTA** (one button, footer links excluded).
- **Required footer** last in both files: brand's mailing address, reason line, unsubscribe link (`https://example.com/unsubscribe?id={{subscriber_id}}`) and preferences link (`https://example.com/preferences?id={{subscriber_id}}`).
- **Banned words:** the house list in `brand/voice-guide.md` *plus* the brand's own list.
- Facts only from the brand's `products.md`. If it isn't there, ask, or leave a visible `[[TODO: ...]]`.
- All the write-email structure, HTML, plain-text, parity and self-check rules.

## Checks

`check_draft.py` reads `brand.txt` and shows the brand it used in its **Brand profile** row. Make sure that row names the right brand before you trust the rest:

```
python .claude/skills/review-email/scripts/check_draft.py drafts/<slug>
```

Backup grep for banned words: add the brand's terms to the house pattern, e.g. for Rise & Crumb:

```
grep -niE "delv|unlock|game.?changer|elevat|revolutionar|synerg|seamless|leverag|supercharg|next.?level|must.?have|act now|limited time|miss out|best ever|guilt.?free|detox|artisanal perfection|magic|to die for|sinful|mouthwatering|superfood|clean eating|sells out fast" drafts/<slug>/email.*
```

## Not brand-aware yet

`personalize-email`, `ab-variants` and `analyze-campaign` still assume Kettlebird (`data/subscribers.csv` has `favorite_tea`, and their scripts read `brand/` only). Don't run them on another brand's draft until they're updated. Say so if the user asks.

## Adding a new brand

Copy `brands/rise-and-crumb/` to `brands/<new-slug>/`, rewrite both files (keep the `## Banned words and phrases` heading and the `## Email footer` table), then run the checker on a test draft and confirm the Brand profile row passes.
