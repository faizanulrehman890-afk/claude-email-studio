# A/B variants: steep-club-launch

Generated 2026-11-14 from `email.txt` / `email.html` (review verdict: PASS).
Each variant replaces the subject, preview text and first paragraph only. Greeting, body, CTA ("Join The Steep Club"), sign-off and footer are unchanged. Every hook leads into the existing second paragraph, which opens "So we started The Steep Club."

## Control (current draft)

- **Subject:** Three teas, one quiet morning a month
- **Preview:** Meet The Steep Club: three seasonal single-origin teas, $28 a month.
- **Opening hook:** There's a moment, just after you pour, when the steam carries the whole tea up to meet you. We wanted to bring you more of those moments, a little different each season.

## Variant A: Curiosity / Story

- **Subject:** The question that started The Steep Club
- **Preview:** It began over the first pot of the day, and the answer changes each season.
- **Opening hook:** We kept asking ourselves the same thing over the first pot of the morning: what should we be drinking right now? The answer changes with the season, and we wanted to share it with you.

## Variant B: Sensory / Tasting-note

- **Subject:** Honeysuckle, pine resin and a little cocoa
- **Preview:** Three winter teas from Fujian, the Wuyi Mountains and Assam, in one box.
- **Opening hook:** Picture a first sip of honeysuckle and fresh hay. Then campfire and pine resin, then malt with a little cocoa. Three teas, three corners of winter, and we wanted them in your kettle.

## Variant C: Direct / Benefit

- **Subject:** Three seasonal teas a month, for $28
- **Preview:** Single-origin, with tasting notes and a brewing card. Skip or cancel any month.
- **Opening hook:** Here's the short version: good tea, chosen for you, arriving each month. We wanted to take the guesswork out of what to brew next.

## Comparison

| Variant | Angle | Subject | Subject chars | Preview chars | Best-fit segment | Hypothesis |
|---|---|---|---|---|---|---|
| Control | Ritual moment | Three teas, one quiet morning a month | 37 | 68 | `active` | The baseline. Calm and specific; it doesn't name the product, so it relies on trust in Kettlebird to earn the open. |
| A | Curiosity / Story | The question that started The Steep Club | 40 | 75 | `new` | We expect new subscribers, who don't know us yet, to open for a "why we made this" story; it doubles as an introduction to who we are. |
| B | Sensory / Tasting-note | Honeysuckle, pine resin and a little cocoa | 42 | 72 | `active` | We expect recent buyers, who already brew with us and want new arrivals, to open for real tasting notes they can almost taste. |
| C | Direct / Benefit | Three seasonal teas a month, for $28 | 36 | 79 | `lapsed` | We expect lapsed readers to respond to a plain, low-pressure offer: price up front and "skip or cancel any month" remove the reasons to hesitate, with no guilt. |

`vip` readers aren't the best fit for any single angle here. We'd send them the control or Variant A, since they want the inside story more than the pitch.

## Facts used

| Claim | Source in brand/products.md |
|---|---|
| The Steep Club | The Steep Club: Name |
| three seasonal (single-origin) teas | What's in each box: 3 seasonal single-origin teas |
| arriving each month / a month | Ships: at the start of each month |
| $28 | Price: $28/month |
| tasting notes and a brewing card | What's in each box: tasting notes and a brewing guide card |
| skip or cancel any month | Commitment: Skip or cancel any month from your account |
| winter teas | Launch box: Winter 2026 |
| honeysuckle, fresh hay | Snow Bud White tasting notes |
| campfire, pine resin | Smoked Pine Lapsang tasting notes |
| malt, a little cocoa | Winter Flush Assam tasting notes |
| Fujian, the Wuyi Mountains, Assam | Launch box origins |

## How to run the test

- Test one thing at a time: subject + preview against the control first (success metric: open rate), then the winning opening hook (success metric: clicks on the one CTA).
- Split each segment evenly between control and variant, and give it enough sends to compare before choosing.
- This repo never sends. Use the `email-outbox` MCP tools (`send_test_email`) for practice sends to `@example.com` only.
