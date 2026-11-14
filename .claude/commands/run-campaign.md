---
description: Run a Kettlebird Tea campaign end to end (draft → audit → personalize → practice send) for drafts/<slug>/
argument-hint: <slug> [optional campaign brief]
allowed-tools: Read, Glob, Grep, Agent, Skill, Bash(python .claude/skills/personalize-email/scripts/personalize.py:*), mcp__email-outbox__send_test_email, mcp__email-outbox__list_outbox, mcp__email-outbox__get_outbox_stats
---

# Run campaign: `$ARGUMENTS`

Run the full campaign pipeline below for one campaign. `CLAUDE.md` wins over anything in this command. Nothing here sends real email: the only "send" is the local `email-outbox` practice outbox.

## Step 0: Parse the arguments

Raw arguments: `$ARGUMENTS`

- **Slug** = the first whitespace-separated word of the arguments. It must match `^[a-z0-9]+(-[a-z0-9]+)*$` (lowercase letters, digits, single hyphens), e.g. `steep-club-launch`, `autumn-newsletter`.
- **Brief** = everything after the slug (optional), e.g. `win-back for lapsed readers, CTA to browse new arrivals`.
- If the arguments are empty or the slug is invalid, stop and print the usage line: `/run-campaign <slug> [optional campaign brief]`. If there's no slug but `drafts/` has folders, list them.

Below, `<slug>` means the parsed slug, never the raw arguments.

Print a one-line plan (`Campaign <slug>: draft → audit → personalize → practice send`) and then run the steps **strictly in order**. Each step must succeed before the next starts. On any stop, print which step stopped, why, and what the user should do next, then end the command. Do not skip, reorder or "work around" a step, and do not fix copy yourself: copy changes belong to `campaign-writer`, sign-off belongs to `campaign-auditor`.

## Step 1: Draft (only if needed)

Check whether `drafts/<slug>/email.html` exists.

- **It exists:** skip drafting. Say `Step 1: draft exists, skipping`. Do not overwrite or rework it.
- **It doesn't exist, and `drafts/<slug>/` doesn't exist either:**
  - If there's no brief, stop and ask for one (email type, audience segment, the one CTA). Don't guess a campaign from the slug alone.
  - Otherwise delegate to the **`campaign-writer`** subagent (Agent tool, `subagent_type: campaign-writer`) with: the slug, the full brief, the folder `drafts/<slug>/`, and a reminder that facts come only from `brand/products.md` (missing facts become visible `[[TODO: ...]]` placeholders).
  - When it returns, confirm both `drafts/<slug>/email.html` and `drafts/<slug>/email.txt` exist. If either is missing, stop.
  - If the writer reports any `[[TODO: ...]]`, stop here and list them: the user has to supply those facts before audit.
- **The folder exists but `email.html` doesn't:** stop. The campaign-writer refuses to write into an existing folder, so tell the user to remove or rename the folder (or add the draft) and re-run.

## Step 2: Audit (hard gate)

Always run a fresh audit, even if an old `review.md` exists.

- Delegate to the **`campaign-auditor`** subagent (Agent tool, `subagent_type: campaign-auditor`) to audit `drafts/<slug>/` and write `drafts/<slug>/review.md`.
- When it returns, **read `drafts/<slug>/review.md` yourself** and find the verdict line (`verdict: **PASS**` or `verdict: **FAIL**`). Don't rely on the subagent's summary alone.
- **Stop immediately** if any of these is true:
  - `review.md` is missing or has no verdict line;
  - the verdict is FAIL, or any table row is `FAIL` / `❌`;
  - `grep -n "\[\[TODO" drafts/<slug>/email.*` finds anything.

  On a stop, list every FAIL as `file:line — issue — suggested fix` from `review.md` and suggest re-running `/run-campaign <slug>` after the fixes. Don't personalize or send anything.
- PASS with WARNs is allowed to continue. Carry the WARNs into the final report as pre-send notes.

## Step 3: Personalize

Use the **`personalize-email`** skill (Skill tool) on `drafts/<slug>`, following its steps. The audit above counts as the approved review it asks for.

- If `drafts/<slug>/segments.json` already exists, keep it unless it breaks the skill's callout rules; otherwise write one per the skill.
- Render with `python .claude/skills/personalize-email/scripts/personalize.py drafts/<slug>` (default: one subscriber per segment).
- **Stop** if the script prints `ABORT` or `FAIL`, or if `segments.json` needs a `[[TODO: ...]]` resolved.
- Note the exact `WROTE ...` lines: those preview pairs (`drafts/<slug>/previews/<segment>-<local>.html` + `.txt`) are the only files sent in Step 4. Ignore older files left in `previews/`.

## Step 4: Practice send (local outbox only)

For each preview pair written in Step 3:

1. Read both files. Take the recipient from the `to=` field in the `PREVIEW ONLY` header on line 1, and the subject from the `Subject:` line of the `.txt`.
2. **Recipient check:** it must be exactly one address matching `^[A-Za-z0-9._%+-]+@example\.com$`. If not, skip that pair and report it by file name only (never echo the address). Never send to any other address, never add CC/BCC, never invent recipients.
3. Call `send_test_email` (email-outbox MCP) with:
   - `to`: that @example.com address
   - `subject`: the subject line
   - `html_body`: the full `.html` preview file contents
   - `text_body`: the full `.txt` preview file contents
   - `campaign_slug`: `<slug>`
4. Record the returned `message_id` and `record` path. If a call is rejected, report the error and carry on with the remaining previews; don't retry with a different address.

Then call `get_outbox_stats` (and `list_outbox` with `campaign_slug: <slug>` for this campaign's rows).

## Final report

Finish with a short summary:

```
Campaign: <slug>
1 Draft         created | existed
2 Audit         PASS (<n> warn)  → drafts/<slug>/review.md
3 Personalize   <n> preview pairs → drafts/<slug>/previews/
4 Practice send <n> sent, <n> skipped  (local outbox only, nothing left this machine)
```

Then: a table of sends (segment, recipient, message_id), the `get_outbox_stats` totals (overall and per campaign), and the pre-send WARNs from `review.md` (for example, the sample mailing address to replace before any real send).
