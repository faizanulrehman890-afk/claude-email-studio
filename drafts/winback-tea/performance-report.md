# Performance report: winback-tea

Generated 2026-11-14 by the analyze-campaign skill.
> **Simulated data.** Numbers come from `data/campaign-metrics.csv` (sample data). This repo never sends real email; the only sends are practice sends in `outbox/`.

## Summary

The `vip` segment won clearly. It had a 9.05% CTR, ahead of `active` at 4.84%, and the gap is significant (p = 0.0247). The segment this win-back was written for, `lapsed`, had the lowest CTR at 2.83% and the highest unsubscribe rate at 0.62%, so it missed the 0.50% guardrail. Across the campaign, 28.59% opened and 3.91% clicked. The most important next step is a subject and preview test on `lapsed`. Once they open, they click at a normal rate. Too few of them open.

## Results by segment and variant

| Segment | Variant | Sent | Opened | Clicked | Unsubs | Open Rate % | CTR % | CTOR % | Unsub Rate % |
|---|---|---|---|---|---|---|---|---|---|
| new | control | 180 | 52 | 6 | 1 | 28.89 | 3.33 | 11.54 | 0.56 |
| active | control | 640 | 237 | 31 | 1 | 37.03 | 4.84 | 13.08 | 0.16 |
| vip | control | 210 | 118 | 19 | 0 | 56.19 | 9.05 | 16.10 | 0.00 |
| lapsed | control | 1450 | 302 | 41 | 9 | 20.83 | 2.83 | 13.58 | 0.62 |

Only one variant (`control`) was sent, so variants can't be compared for this campaign.

## Campaign total

| Sent | Opened | Clicked | Unsubs | Open Rate % | CTR % | CTOR % | Unsub Rate % |
|---|---|---|---|---|---|---|---|
| 2480 | 709 | 97 | 11 | 28.59 | 3.91 | 13.68 | 0.44 |

## Winner

- **Winner:** `vip` / `control`: CTR 9.05%, CTOR 16.10%, Open 56.19%, Unsub 0.00%
- **Runner-up:** `active` / `control`: CTR 4.84%
- **CTR gap:** 4.20 percentage points
- **Two-proportion z-test (CTR, winner vs runner-up):** z = 2.25, p = 0.0247 (significant at 95%)
- Excluded `new` / `control`: unsub rate 0.56% > guardrail 0.50%
- Excluded `lapsed` / `control`: unsub rate 0.62% > guardrail 0.50%

The win is real, but it comes from the readers who need winning back least. VIPs open and click almost anything from us. This result doesn't show that the win-back message works.

## What the numbers say

- **Lapsed readers don't open, but the body works when they do.** `lapsed` has the lowest open rate (20.83%), yet its CTOR (13.58%) is close to the campaign's 13.68% and above `active` (13.08%). The weak point is the subject and preview, not the three-tea list or the CTA.
- **The guardrail is being crossed by the very readers we want back.** `lapsed` unsubscribes ran at 0.62% (9 of 1450), the highest of any segment.
- **This email isn't right for new subscribers.** `new` had the lowest CTOR (11.54%) and a 0.56% unsubscribe rate on a small sample of 180. A "we've missed you" email reads oddly to someone who joined last month.
- **VIPs respond very well.** A 56.19% open rate and 0.00% unsubscribes suggest VIPs want to hear from us often. They'd likely do even better with a message written for them.
- **Active readers are steady.** `active` had a 4.84% CTR and the lowest non-zero unsubscribe rate (0.16%).

## Recommendations for the next campaign

1. **Test the subject and preview on `lapsed` only.** Run the `ab-variants` skill on `winback-tea` and send the control plus one or two variants to `lapsed`. Measure open rate against today's 20.83%, and keep the body unchanged so CTOR (13.58%) stays a fair comparison.
2. **Leave `new` out of win-back sends.** Send them the `welcome-series` draft instead, which is what CLAUDE.md says new subscribers need. Track whether their unsubscribe rate falls below today's 0.56%.
3. **Watch the `lapsed` unsubscribe rate as a hard limit.** If the next test's unsubscribe rate stays above the 0.50% guardrail (today 0.62%), make the email gentler and less frequent rather than more persuasive. Keep the "no rush" tone and add no urgency.
4. **Give `vip` its own email instead of the win-back.** Their 9.05% CTR and 0.00% unsubscribes show the attention is there. A thank-you or inside-story email (the `vip` row in CLAUDE.md) is a better fit than "we've missed you". Use only facts from `brand/products.md`. No invented early-access offers.
5. **Use bigger samples before calling winners within a segment.** `new` (180) and `vip` (210) are small. Aim for at least a few hundred per variant so a z-test can separate them.

## Data checks

- Metrics rows: 4, validation: passed
- Outbox (`get_outbox_stats` / `list_outbox`): 4 practice sends for `winback-tea` (5 in the outbox overall). One recipient per segment: ada.bloom@example.com (`new`), dev.patel@example.com (`active`), hugo.martin@example.com (`vip`), liam.brooks@example.com (`lapsed`). Every subject matches the `control` subject in `email.txt`. Script result: every metrics row has a matching practice send, all subjects match the draft, all recipients are @example.com.
- All figures produced by `.claude/skills/analyze-campaign/scripts/calc_metrics.py`; none calculated by hand.
