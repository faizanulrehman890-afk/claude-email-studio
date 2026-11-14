# Kettlebird Tea — Email Studio

This repo is where we write Kettlebird Tea's marketing emails. Drafts only: nothing here sends email.

## Who we are

Kettlebird Tea is a small loose-leaf tea company. We source single-origin teas from small farms and sell them direct, mostly by email and our online shop.

## Brand voice (summary)

Full guide: `brand/voice-guide.md`.

- **Warm.** Like a friend who's put the kettle on for you.
- **Sensory.** Show the tea: the color of the liquor, the smell of the leaf, the steam.
- **Unhurried.** Short, calm sentences. No countdowns, no pressure, no shouting.
- **Never hypey.** No exclamation-mark pileups, no ALL CAPS, no superlatives we can't back up.

## Folder layout

```
CLAUDE.md                     project rules (this file)
brand/voice-guide.md          tone, vocabulary, good vs bad copy, formatting
brand/products.md             the source of truth for product facts and prices
data/subscribers.csv          FAKE sample subscribers for testing merge tags
drafts/<slug>/email.html      HTML version of each campaign
drafts/<slug>/email.txt       plain-text version of each campaign
notes/                        research and decision notes
.claude/skills/write-email/   the skill for drafting emails (use it)
```

## Audience segments

Every subscriber in `data/subscribers.csv` has one `segment`:

| Segment | Who | What they need from us |
|---|---|---|
| `new` | Subscribed in the last 30 days, no order yet | A welcome; who we are; an easy first tea |
| `active` | Ordered in the last 90 days | Stories, brewing tips, new arrivals |
| `vip` | 5+ orders or a current subscription | Early access, thanks, the inside story |
| `lapsed` | No order in 180+ days | A gentle hello and what's new, without guilt |

## Hard rules

1. **Use the `write-email` skill** for every marketing email.
2. **Banned words** never appear in any copy: delve, unlock, game-changer, elevate, revolutionary, synergy, seamless, leverage, supercharge, "act now", "limited time only", "don't miss out", "best ever". The full list is in `brand/voice-guide.md`.
3. **Every email has a footer** with the unsubscribe link, the preferences link, the reason they're receiving it, and our mailing address:
   Kettlebird Tea, 14 Wren Lane, Suite 2, Portland, OR 97201, USA *(sample address: replace before sending)*
4. **Only `@example.com`** for email addresses and **only `example.com`** for links, in drafts, data and tests. Never a real customer address or a live URL.
5. **Facts come from `brand/products.md`.** Don't invent prices, dates, discounts or contents. If it isn't there, ask.
6. **One email, one call to action.**
7. **Never send.** No API keys in files, no calls to an email provider from this repo.
