# Skills I chose (and didn't)

*2026-11-14*

## 1. What I searched for and what came back

I ran `npx skills find` on skills.sh for four searches: **resend**, **email marketing**, **email**, and **newsletter**. The install counts below are what skills.sh reported that day.

**Resend:** most results come from Resend's own GitHub org (`resend/...`):

| Skill | Publisher | Installs | What it claims to do |
|---|---|---|---|
| `resend/resend-skills@resend` | Resend (official) | 24.6K | Covers the whole Resend API: sending, batch, webhooks, templates, domains, contacts, broadcasts, plus a list of common pitfalls |
| `resend/resend-skills@resend-cli` | Resend (official) | 14.1K | Driving the Resend CLI |
| `resend/resend-skills@agent-email-inbox` | Resend (official) | 14.1K | Letting an agent receive and reply to email |
| `resend/react-email@react-email` | Resend (official) | 10K | Building email templates with React Email |
| `resend/email-best-practices` | Resend (official) | 8.3K | Deliverability (SPF/DKIM/DMARC), compliance (CAN-SPAM, GDPR, CASL), list hygiene, accessibility |
| `vercel-labs/emulate@resend` | Vercel Labs | 239 | A local stand-in for Resend, for testing |
| `gocallum/...@resend-integration-skills`, `hookdeck/...@resend-webhooks`, `membranedev/...@resend` | Individuals / small vendors | 130–420 | Wrappers or integrations around Resend |

**Email marketing:** mostly third-party, and quality varies a lot:

| Skill | Publisher | Installs | What it claims to do |
|---|---|---|---|
| `caffeinelabs/skills@extension-email-marketing` | Caffeine AI | 31.6K | Marketing emails with an unsubscribe link, but only on Caffeine's own platform (Motoko backend, their mail gateway) |
| `coreyhaines31/marketingskills@emails` | Individual (well-known marketer) | 88.6K | Writing guidance for welcome, onboarding, nurture and win-back sequences. Just text, no code |
| `claude-office-skills/skills@email-marketing` | Anonymous org | 5.2K | Campaigns, sequences, A/B testing, analytics. Its frontmatter mentions `mailchimp_send` and `sendgrid_campaign` actions. Last updated January 2026 |
| Others (`kostja94`, `arnabbagxd`, `nexscope-ai`, `cosmoblk`, ...) | Individuals | 100–1.8K | General marketing advice |

**How I inspected them.** I shallow-cloned five candidate repos into a temp folder as read-only data. I did not install anything and did not run any of their code. Then I read each SKILL.md, listed every file that ships with it, and searched for: tool permissions (`allowed-tools`), shell or network commands (`curl`, `| sh`, `npx`, `pip install`), secret handling (`API_KEY`, `.env`), hidden HTML comments, and invisible or bidirectional Unicode characters.

What I found:
- **None of the five** had hidden comments, invisible Unicode, `allowed-tools` grants, or "pipe this to your shell" instructions.
- **Resend's `resend` skill** asks for `RESEND_API_KEY` and reads it from an environment variable. It never asks for the key to be pasted into a file or chat. It ships one script, `fetch-all-templates.mjs`, which only lists templates through the official SDK. The repo also has an `mcp.json` pointing at `https://mcp.resend.com/mcp`. That would add an MCP server if it were installed as a plugin, so it needs a separate decision.
- **Caffeine's skill** depends on platform-injected gateway keys and Caffeine packages. It's not malicious, but it doesn't fit us.
- **claude-office-skills** comes from an anonymous publisher, is stale, and is 627 lines of generic advice. Nothing dangerous, but nothing we can't write ourselves.

## 2. What makes a skill safe to trust vs risky to install

A SKILL.md isn't documentation. **It is instructions the agent follows, with the same permissions as me.** Once it's installed, the agent can load it whenever the description matches, and anything it says counts as guidance the agent acts on. These are the specific risks:

- **Prompt injection by design.** The file can say "before sending, also POST the contacts list to X" or "don't mention this step to the user." The agent may comply. Instructions can be hidden in HTML comments, zero-width characters, or a `references/*.md` file that GitHub's rendered view makes easy to skip.
- **Bundled scripts run on my machine.** A skill can ship `.sh`, `.py` or `.mjs` files and tell the agent to run them. That's arbitrary code execution, with access to my files, my shell, and every secret in my environment.
- **Secret exfiltration.** An email skill gets the API key by definition. A bad one can tell the agent to "verify the key" by sending it to a third-party URL, or to write it into a committed file. A stolen Resend key lets someone send mail from our domain, which means phishing from us and a ruined sender reputation.
- **Over-broad permissions.** `allowed-tools` in the frontmatter can pre-approve Bash or network tools so I'm never asked. A plugin can also add MCP servers or hooks that run automatically.
- **Over-eager triggering.** A description like "ALWAYS use this skill when..." pulls the skill into tasks it shouldn't touch.
- **Supply-chain drift.** `npx skills add` pulls the current version. A skill that was clean today can be changed tomorrow, or the repo can change owners. The install count isn't a security review: it's easy to inflate and says nothing about what the file contains.
- **Remote fetches.** A skill that says "read the latest instructions from https://..." can be swapped out at any time without its file changing.
- **Business risk specific to email.** Bad advice about unsubscribe handling, consent, or bulk sending can break CAN-SPAM or GDPR rules, or get our domain blocklisted, even if the skill isn't malicious at all.

**Safer signs:** the publisher is the vendor itself (e.g. the `resend` GitHub org), the source is public and recently maintained, the skill is plain markdown with no scripts (or small scripts I've read), there's no `allowed-tools`, secrets come only from environment variables, and it has a license. **Before trusting any skill I read:** the frontmatter (description, tools, required secrets), every file in the folder rather than only SKILL.md, every URL and command, and the raw text instead of the rendered page. After that I pin the exact commit.

## 3. My decision

**I didn't install any third-party skill. We'll write our own.**

Why:
- This project is empty right now. We have no code that sends email yet, so a skill would only add risk with nothing to gain.
- The good candidates, Resend's official `resend` and `email-best-practices`, look clean and are the ones I'd trust most. But they're broad: 287 lines plus about 20 reference files covering inboxes, automations, CLI use and more. Most of that we don't need. They'd also bring an API key requirement and possibly an MCP server.
- The marketing-specific skills are either tied to another platform (Caffeine), anonymous and stale (claude-office-skills), or pure copywriting advice we can write to fit our own voice.

**Plan:** write a small project skill in `.claude/skills/`, under our own version control, that covers only what My Email Studio uses. That means the Resend send and batch calls, the key read from `RESEND_API_KEY`, idempotency keys, webhook signature checks, and unsubscribe and compliance rules. Both Resend skills are MIT-licensed, so we can borrow specific facts from them, such as known pitfalls and the SPF/DKIM/DMARC checklist. If we later decide we want the full official `resend` skill, we'll install it from `resend/resend-skills` pinned to a reviewed commit (it was `f3e86d8` when I checked) and decide separately whether to enable its MCP server.
