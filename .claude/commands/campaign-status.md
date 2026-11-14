---
description: Quick read-only dashboard of every campaign in drafts/ plus practice-outbox counts
allowed-tools: Read, Glob, Grep, Bash(ls:*), mcp__email-outbox__get_outbox_stats
---

# Campaign status

Give a quick dashboard of all campaigns. This command is **read-only**: don't create, edit or delete any file, don't run subagents or skills, and don't send anything.

## Gather

1. List every folder in `drafts/`. For each `<slug>`, check:
   - **Draft:** whether `email.html` and `email.txt` exist.
   - **Audit:** whether `review.md` exists; if so, read its header to get the verdict (`PASS` / `FAIL`), the fail/warn counts, and the `Reviewed <date>` date. Treat a review as **stale** if `email.html` or `email.txt` is newer than `review.md`.
   - **TODOs:** count `[[TODO` occurrences in `email.html` / `email.txt`.
   - **Previews:** count the `.html` files in `previews/` (0 if the folder is missing) and whether `segments.json` exists.
2. Call `get_outbox_stats` once for the practice-send counts per campaign. Outbox folders with no matching `drafts/` folder still get a row.

## Report

One table, one row per campaign, sorted by slug:

| Campaign | Draft | Audit | TODOs | Previews | Practice sends | Next step |
|---|---|---|---|---|---|---|

- **Draft:** `html + txt`, `html only`, `txt only` or `none`.
- **Audit:** e.g. `PASS (0 fail, 4 warn) 2026-11-14`, `FAIL (2 fail)`, `stale`, or `not audited`.
- **Next step:** the first unfinished stage: `draft` → `audit` (or `fix FAILs`) → `personalize` → `practice send` → `ready for human sign-off`. Suggest `/run-campaign <slug>` where it applies.

Below the table, print the outbox total from `get_outbox_stats`, and a one-line reminder that the outbox is local practice only. Keep it short: no file dumps, no review details beyond the counts.
