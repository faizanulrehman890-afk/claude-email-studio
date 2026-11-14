# Email Studio

An AI-assisted, multi-brand email marketing studio built with [Claude Code](https://claude.com/claude-code).

It writes, checks, personalizes and "practice-sends" marketing emails for **Kettlebird Tea**, a small (fictional) loose-leaf tea company, and for any other brand that has a profile in `brands/` (the sample is **Rise & Crumb**, a sourdough bakery).

**It produces drafts only.** Nothing in this repo sends real email. The only "send" writes files to a local `outbox/` folder, and only to `@example.com` addresses.

---

## How it works, in one paragraph

You ask Claude Code for a campaign. Claude follows the house rules in `CLAUDE.md`. A **writer** subagent drafts a matched HTML and plain-text email using the `write-email` skill and the brand's voice guide and product facts. A separate **auditor** subagent checks the draft with a script plus a manual review and writes a PASS/FAIL report. If it passes, the `personalize-email` skill renders one preview per audience segment, and those previews go to a local **practice outbox** through an MCP server. Along the way, **hooks** written in plain Python check every file Claude writes and every commit you make. The model writes the copy and makes the judgment calls. The code enforces the hard limits.

---

## Architecture

```
                        CLAUDE.md  (hard rules, brand, segments)
                             │  read by everything below
                             ▼
  /run-campaign <slug>  ─────────────────────────────────────────────┐
     │                                                               │
     ├─ 1 Draft ──► campaign-writer subagent ──► write-email skill   │
     │                 (switch-brand skill for non-Kettlebird brands) │
     │                                                               │
     ├─ 2 Audit ──► campaign-auditor subagent ─► review-email skill  │
     │                 └─ check_draft.py (script) + manual checks    │
     │                 └─ writes drafts/<slug>/review.md   (gate)    │
     │                                                               │
     ├─ 3 Personalize ─► personalize-email skill ─► personalize.py   │
     │                                                               │
     └─ 4 Practice send ─► email-outbox MCP server ─► outbox/<slug>/ │
                                                                     │
  /campaign-status  ── read-only dashboard of drafts/ + outbox stats ┘

  Always on, outside the model:
    PostToolUse hook  (.claude/hooks/guard_drafts.py)   every Write/Edit in drafts/
    Git pre-commit    (scripts/pre_commit_audit.py)     every git commit
```

### `CLAUDE.md`: the rulebook

Loaded into every Claude Code session. It names the brand voice, the four audience segments (`new`, `active`, `vip`, `lapsed`) and seven hard rules: use the `write-email` skill, no banned words, a full footer on every email, `example.com` only, facts only from `products.md`, one call to action per email, and never send for real.

### Brand profiles

| Path | What it holds |
|---|---|
| `brand/voice-guide.md` | Kettlebird tone, vocabulary, banned words, good vs bad copy |
| `brand/products.md` | Kettlebird product facts and prices: the only source of facts |
| `brands/<brand>/` | Another brand's `voice-guide.md` and `products.md` (incl. its email footer) |
| `drafts/<slug>/brand.txt` | Marks a draft as belonging to another brand |

Kettlebird is the default. For other brands, the brand's own files replace `brand/`, its banned words are **added** to the house list, and every hard rule still applies.

### Skills (`.claude/skills/`)

Skills are step-by-step instructions Claude loads when a request matches them. Several include a small script for the parts that must be exact.

| Skill | Job | Script |
|---|---|---|
| `write-email` | Draft an `email.html` + `email.txt` pair in `drafts/<slug>/` | — |
| `review-email` | Strict QA: banned words, facts, subject/preview/CTA/footer, mobile HTML, links, text parity | `check_draft.py` |
| `personalize-email` | Fill merge tags with safe fallbacks, add a segment line, write per-subscriber previews | `personalize.py` |
| `ab-variants` | Subject line, preview text and opening-hook variants, with a comparison table | `check_variants.py` |
| `analyze-campaign` | Open rate, CTR, click-to-open and unsubscribe rate from sample metrics, plus a report | `calc_metrics.py` |
| `switch-brand` | Draft or audit for a brand other than Kettlebird, with all hard rules still on | (uses `scripts/brand_profile.py`) |

### Subagents (`.claude/agents/`)

Two subagents with separate jobs, so no one grades their own work:

- **`campaign-writer`** drafts a complete campaign into a new `drafts/<slug>/` folder. When a fact is missing it leaves a visible `[[TODO: ...]]` instead of guessing. It never signs off its own draft.
- **`campaign-auditor`** audits a draft and writes `drafts/<slug>/review.md` with a verdict. It is read-only toward the email itself: it reports problems and never fixes them.

### Hooks

| Hook | When it runs | What it blocks |
|---|---|---|
| `PostToolUse` → `.claude/hooks/guard_drafts.py` (set in `.claude/settings.json`) | After every Claude `Write`/`Edit` to a file in `drafts/` | Non-`@example.com` addresses, non-`example.com` links, banned words. Exit code 2 sends the problem back to Claude to fix. |
| Git `pre-commit` → `scripts/pre_commit_audit.py` (installed by `scripts/install_hooks.py`) | Every `git commit`, on the staged content | Same address/link/banned-word checks (brand-aware), plus `.env` files, private keys and anything that looks like an API key |

### MCP server: `email-outbox` (`mcp/email_server.py`)

A small Python MCP server (standard library only, no network) registered in `.mcp.json`. Its three tools:

- `send_test_email(to, subject, html_body, text_body, campaign_slug)` saves a JSON record and an HTML file to `outbox/<slug>/`. It rejects any recipient that isn't one address at exactly `@example.com`, and any slug that could write outside `outbox/`.
- `list_outbox(campaign_slug)` lists saved practice sends.
- `get_outbox_stats()` returns totals overall and per campaign.

`outbox/` is git-ignored.

### Slash commands (`.claude/commands/`)

- **`/run-campaign <slug> [brief]`** runs the whole pipeline in order: draft (only if none exists) → audit (a hard gate: any FAIL or TODO stops the run) → personalize → practice send → summary report.
- **`/campaign-status`** prints a read-only table of every campaign: draft files, audit verdict (and whether it's stale), TODOs, previews, practice sends and the next step.

---

## Quick start for teammates

**You need:** Git, Python 3 (standard library only, nothing to `pip install`), and Claude Code.

1. **Clone and open the repo**
   ```sh
   git clone <repo-url> My-Email-Studio
   cd My-Email-Studio
   ```

2. **Install the Git pre-commit hook** (once per clone)
   ```sh
   python scripts/install_hooks.py
   ```
   It's safe to re-run. If you already have a different pre-commit hook, it's backed up to `pre-commit.backup` first.

3. **Start Claude Code and enable the MCP server**
   ```sh
   claude
   ```
   Claude Code finds `.mcp.json` and asks whether to trust the project's `email-outbox` server. Approve it. Run `/mcp` to check that `email-outbox` shows as connected. The `PostToolUse` hook in `.claude/settings.json` is active automatically.

4. **Check where things stand**
   ```
   /campaign-status
   ```

5. **Run a campaign**
   ```
   /run-campaign autumn-newsletter newsletter for active readers, CTA to browse new arrivals
   ```
   For another brand, mention it in the brief (for example `--brand rise-and-crumb`) and the `switch-brand` skill takes over.

**Useful direct commands**

```sh
python scripts/pre_commit_audit.py --all                                  # audit every tracked file
python .claude/skills/review-email/scripts/check_draft.py drafts/<slug>   # mechanical QA for one draft
```

---

## Safety and deterministic guardrails

Language models are good at writing warm, specific copy and at judging tone. They are not reliable at *always* following a rule. A model can miss a banned word, accept a plausible-looking real address, or forget a footer. So this studio splits the work:

| Handled by the model (judgment) | Enforced by code (hard boundaries) |
|---|---|
| Writing copy in the brand voice | Only `@example.com` addresses: hook, pre-commit, MCP server |
| Picking which facts and products fit the brief | Only `example.com` links: hook, pre-commit, `check_draft.py` |
| Tone, warmth, pacing, "is this hypey?" | Banned words per brand: hook, pre-commit, `check_draft.py` |
| Segment-specific lines | No secrets or keys committed: pre-commit |
| Interpreting audit findings | Nothing leaves the machine: the outbox server has no network code |
| Recommending next steps from metrics | Metrics math is done by `calc_metrics.py`, never by the model |

The rules that matter most are enforced **more than once, at different layers**: in the instructions (`CLAUDE.md`, skills), when a file is written (`PostToolUse` hook), when work is committed (`pre-commit`), and at the point of "sending" (MCP server validation). If the model drifts, a script catches it. The instructions say *what good looks like*. The code makes sure the worst outcomes can't happen.

Other design choices that keep things safe:

- **Separation of duties.** The writer never approves its own work. The auditor never edits the draft.
- **Missing facts are visible.** Unknown prices or dates become `[[TODO: ...]]` markers, and `/run-campaign` won't go past the audit while any remain.
- **Fake data only.** `data/subscribers.csv` and `data/campaign-metrics.csv` are samples. The footer address is a placeholder to replace before any real use.
- **Vetting third-party skills.** `notes/skills-i-chose.md` records how outside skills were inspected before any were trusted.

---

## Current campaigns

| Campaign | Brand | Audit | Previews | Practice sends |
|---|---|---|---|---|
| `rise-and-crumb-weekend` | Rise & Crumb | PASS (0 fail, 4 warn) | 0 | 0 |
| `steep-club-launch` | Kettlebird | PASS (0 fail, 4 warn) | 4 | 1 |
| `welcome-series` | Kettlebird | PASS (0 fail, 4 warn) | 0 | 0 |
| `winback-tea` | Kettlebird | PASS (0 fail, 5 warn) | 4 | 4 |

Run `/campaign-status` for the live version.

---

## Repo layout

```
CLAUDE.md                       project rules
README.md                       this file
.mcp.json                       registers the email-outbox MCP server
.claude/settings.json           PostToolUse hook config
.claude/hooks/guard_drafts.py   draft guardrail hook
.claude/skills/<skill>/         skills (+ their scripts)
.claude/agents/                 campaign-writer, campaign-auditor
.claude/commands/               /run-campaign, /campaign-status
brand/                          Kettlebird voice guide + product facts
brands/<brand>/                 other brand profiles
data/                           fake subscribers + sample campaign metrics
drafts/<slug>/                  email.html, email.txt, review.md, previews/, ...
mcp/email_server.py             local practice-outbox MCP server
scripts/                        pre-commit audit, hook installer, brand profile loader
notes/                          research and decision notes
outbox/                         practice sends (git-ignored)
```
