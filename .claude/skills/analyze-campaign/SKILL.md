---
name: analyze-campaign
description: Analyze, report on, or evaluate the performance of a Kettlebird Tea campaign in drafts/<slug>/ using the simulated engagement numbers in data/campaign-metrics.csv, cross-checked against practice-outbox records. Computes open rate, CTR, click-to-open rate and unsubscribe rate with a script (never by mental math), picks the winning segment/variant, and saves an actionable drafts/<slug>/performance-report.md. Use when the user asks how a campaign performed, for campaign metrics, results, stats, a performance report, which segment or variant won, or what to change next time. Not for writing emails (write-email), QA (review-email), A/B ideas (ab-variants) or sending.
---

# Analyze a Kettlebird Tea campaign

This skill writes **one file**: `drafts/<slug>/performance-report.md`. It never edits `email.html`, `email.txt` or the metrics data, never sends email, and never calls an email provider or analytics service.

**The numbers are simulated.** `data/campaign-metrics.csv` is sample data for practising analysis. Nothing in this repo sends real email (CLAUDE.md rule 7), so no real engagement exists. Every report says so at the top.

## Step 1: Load the sources (required)

1. Work out the slug. If the user didn't name one and `data/campaign-metrics.csv` has more than one `campaign_slug`, ask.
2. Read:
   - `CLAUDE.md`: segments, hard rules. They win over this skill if they conflict.
   - `data/campaign-metrics.csv`: columns `campaign_slug,segment,variant,sent_count,opened_count,clicked_count,unsubscribed_count`. `variant` is `control` (the draft as written) or a capital letter matching `## Variant X` in `drafts/<slug>/ab-variants.md`.
   - `drafts/<slug>/email.txt`: the subject, the one CTA and the email type, so recommendations fit the campaign.
   - `drafts/<slug>/ab-variants.md` if it exists: the angle and hypothesis behind each variant.
   - `brand/voice-guide.md`: the report lives in `drafts/`, and the `guard_drafts.py` hook scans it for banned words. Recommendations must also respect the voice (no urgency tactics, no hype).
   - `brand/products.md`: only if a recommendation mentions a product, price or offer. Don't invent discounts or offers (rule 5).

If the slug has no rows in the CSV, stop and tell the user. Don't make up numbers.

## Step 2: Check the practice outbox (required)

Use the `email-outbox` MCP tools. They only read local files.

1. `get_outbox_stats`: note the total and the count for this slug.
2. `list_outbox` with `campaign_slug: "<slug>"`: copy the JSON result exactly.

You'll pass that JSON to the script in Step 3, which maps each recipient to a segment through `data/subscribers.csv` and each subject to a variant through `email.txt` / `ab-variants.md`. If the outbox has no sends for the slug, carry on, but list "not practice-sent" under Data checks in the report.

## Step 3: Compute every number with the script (required)

**Never calculate a rate, sum, difference or percentage yourself.** Each number in the report must be copied from this script's output:

```bash
python .claude/skills/analyze-campaign/scripts/calc_metrics.py <slug> --outbox-json - <<'EOF'
<paste the list_outbox JSON here>
EOF
```

(Without an outbox check: `python .claude/skills/analyze-campaign/scripts/calc_metrics.py <slug>`. Add `--format json` if you need the numbers in machine-readable form.)

The script is standard-library only. It:

- validates every row (whole numbers, `opened ≤ sent`, `clicked ≤ opened`, `unsubscribed ≤ sent`, known segment, no duplicates, `@example.com` only) and exits `1` with a list of problems if any fail,
- computes, from exact fractions rounded half-up to 2 dp:
  - **Open Rate %** = opened / sent × 100
  - **CTR %** = clicked / sent × 100
  - **CTOR %** = clicked / opened × 100
  - **Unsubscribe Rate %** = unsubscribed / sent × 100
- rolls up by segment, by variant and for the campaign, using summed counts (it never averages percentages),
- picks the **winner**: highest CTR (the one CTA is the goal of every email, rule 6) among rows with `sent ≥ 100` and unsubscribe rate `≤ 0.5%`. Ties go to CTOR, then the lower unsubscribe rate. It reports the runner-up, the CTR gap and a two-proportion z-test,
- with `--outbox-json`, lists each practice send's segment and variant and flags mismatches, then exits `1` if any.

Fix validation errors by asking the user. Never edit the metrics yourself to make them pass. If the outbox check reports issues, list them in the report. They don't block it.

## Step 4: Interpret, then write `drafts/<slug>/performance-report.md`

Read the numbers before writing:

- **Winner vs goal.** The overall winner may not be the segment the campaign was made for (for example, a win-back aimed at `lapsed`). Report the script's winner, then say how the target segment did.
- **Significance.** If the z-test p ≥ 0.05, call it a lead, not a win, and recommend a larger test.
- **Guardrails.** A row left out for unsubscribes is a warning sign, especially from `new` or `lapsed` readers.
- **Variants.** If only `control` exists, no variant won. Say so and recommend `ab-variants` for next time.
- **CTOR vs open rate.** High opens with low CTOR points to the body or CTA. Low opens with high CTOR points to the subject/preview.

Use this layout:

```markdown
# Performance report: <slug>

Generated <YYYY-MM-DD> by the analyze-campaign skill.
> **Simulated data.** Numbers come from `data/campaign-metrics.csv` (sample data). This repo never sends real email; the only sends are practice sends in `outbox/`.

## Summary

<3–4 sentences: the winning segment/variant with its CTR, how the target segment did, the campaign-wide open rate and CTR, and the single most important next step.>

## Results by segment and variant

<the script's "By segment and variant" table, copied exactly>

## Campaign total

<the script's total table, copied exactly>

## Winner

<winner, runner-up, CTR gap, z-test line and any excluded rows, copied from the script, then 1–2 sentences on what it means>

## What the numbers say

<3–5 bullets, each tied to a specific number from the tables>

## Recommendations for the next campaign

<3–5 numbered, concrete actions: who, what to change, how to measure it. Each one points to a number above. Respect the brand voice and the one-CTA rule; no discounts or offers unless they're in products.md.>

## Data checks

- Metrics rows: <n>, validation: passed
- Outbox (`get_outbox_stats` / `list_outbox`): <count> practice sends for `<slug>`; <OK line or issues from the script>
- All figures produced by `.claude/skills/analyze-campaign/scripts/calc_metrics.py`; none calculated by hand.
```

Keep it plain and calm: short sentences, no exclamation marks, no ALL CAPS, no banned words (the hook checks, but write it clean the first time).

## Step 5: Verify (required)

1. Re-run the script and check that every number in the report appears in its output. A quick way is to grep each percentage from the report against the script output:
   ```bash
   python .claude/skills/analyze-campaign/scripts/calc_metrics.py <slug> > /tmp/metrics.md
   grep -oE '[0-9]+\.[0-9]{2}' drafts/<slug>/performance-report.md | sort -u | while read n; do grep -q "$n" /tmp/metrics.md || echo "NOT FROM SCRIPT: $n"; done
   ```
   (Use the session scratchpad instead of `/tmp` when one is available.) No output means every 2-dp figure traces to the script.
2. Make sure the `guard_drafts.py` hook raised nothing when the report was written.
3. Check by reading:
   - [ ] The simulated-data notice is at the top.
   - [ ] The winner matches the script, and significance is described honestly.
   - [ ] Every recommendation names a segment or variant and a number.
   - [ ] No invented facts, offers or dates.

## Step 6: Report back

Tell the user briefly: the file path, the winner with its CTR, whether it's statistically significant, the top recommendation, and any outbox or data-check issues.
