#!/usr/bin/env python3
"""Claude Code hook: guardrails for files written or edited inside drafts/.

Runs on PostToolUse for Write|Edit. Reads the hook payload (JSON) from stdin,
and if the touched file lives under drafts/, re-reads the file from disk and
checks it against the project's hard rules:

  * Only @example.com email addresses (CLAUDE.md rule 4).
  * Only example.com links (CLAUDE.md rule 4).
  * No banned words or phrases (CLAUDE.md rule 2, brand/voice-guide.md).
    Applied to the email copy itself (.html / .txt), not to QA notes such as
    review.md, which may need to name a banned word to report on it.

Exit codes (Claude Code hook protocol):
  0  nothing to report (or the file is not a draft)
  2  violation found; the stderr message is fed back to Claude to fix
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Make stderr safe for any characters on Windows consoles.
try:
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ALLOWED_EMAIL_DOMAIN = "example.com"
ALLOWED_URL_HOST = "example.com"  # subdomains of example.com are also allowed
COPY_SUFFIXES = {".html", ".htm", ".txt", ".md"}
COPY_EXCLUDE_NAMES = {"review.md"}  # QA reports may quote banned words

# Used if brand/voice-guide.md can't be read or parsed.
FALLBACK_BANNED = [
    "delve", "unlock", "game-changer", "game changer", "elevate", "revolutionary",
    "synergy", "seamless", "leverage", "supercharge", "next-level", "must-have",
    "act now", "limited time only", "don't miss out", "best ever", "guilt-free",
    "detox",
]
# Always checked, in addition to the voice guide's list.
EXTRA_BANNED = ["limited time"]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@([A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+)")
URL_RE = re.compile(
    r"(?:\b(?:https?|ftp)://|(?<![\w/@.])//|\bwww\.)([A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+)",
    re.IGNORECASE,
)


def project_dir() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[2]


def load_banned(root: Path) -> list[str]:
    """Pull the bullet list under '## Banned words and phrases' in the voice guide."""
    guide = root / "brand" / "voice-guide.md"
    try:
        text = guide.read_text(encoding="utf-8")
    except OSError:
        return FALLBACK_BANNED + EXTRA_BANNED

    m = re.search(r"^##\s+Banned words and phrases\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return FALLBACK_BANNED + EXTRA_BANNED

    terms: list[str] = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        item = re.sub(r"\(.*?\)", "", line[2:])  # drop "(we make no health claims)"
        for part in item.split("/"):  # "game-changer / game changer"
            term = part.strip().strip('"“”').strip()
            if term:
                terms.append(term.lower())
    return (terms or FALLBACK_BANNED) + EXTRA_BANNED


def term_pattern(term: str) -> re.Pattern[str]:
    """Case-insensitive pattern that also catches other forms (unlocks, elevated, leveraging)."""
    words = re.split(r"[\s\-]+", term.replace("’", "'"))
    parts = [re.escape(w).replace("'", "['’]") for w in words]
    if len(parts) == 1:
        stem = parts[0]
        if len(stem) > 4 and stem.endswith("e"):
            stem = stem[:-1]  # elevate -> elevat(e|ed|ing|ion)
        body = stem + r"\w*"
    else:
        body = r"[\s\-]+".join(parts)
    return re.compile(r"(?<![\w])" + body + r"(?![\w])", re.IGNORECASE)


def host_allowed(host: str) -> bool:
    host = host.lower().rstrip(".")
    return host == ALLOWED_URL_HOST or host.endswith("." + ALLOWED_URL_HOST)


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def main() -> int:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0  # not our problem; never break the session on bad input

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or (payload.get("tool_response") or {}).get("filePath")
    if not file_path:
        return 0

    root = project_dir()
    target = Path(file_path)
    if not target.is_absolute():
        target = Path(payload.get("cwd") or root) / target
    target = target.resolve()

    drafts = (root / "drafts").resolve()
    try:
        rel = target.relative_to(drafts)
    except ValueError:
        return 0  # not a draft: allow

    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        # Fall back to what the tool tried to write.
        text = tool_input.get("content") or tool_input.get("new_string") or ""

    problems: list[str] = []

    for m in EMAIL_RE.finditer(text):
        if m.group(1).lower() != ALLOWED_EMAIL_DOMAIN:
            problems.append(
                f"line {line_of(text, m.start())}: email address '{m.group(0)}' "
                f"is not @{ALLOWED_EMAIL_DOMAIN}"
            )

    for m in URL_RE.finditer(text):
        if not host_allowed(m.group(1)):
            problems.append(
                f"line {line_of(text, m.start())}: link to '{m.group(1)}' "
                f"is not {ALLOWED_URL_HOST}"
            )

    if target.suffix.lower() in COPY_SUFFIXES and target.name.lower() not in COPY_EXCLUDE_NAMES:
        for term in dict.fromkeys(load_banned(root)):
            for m in term_pattern(term).finditer(text):
                problems.append(
                    f"line {line_of(text, m.start())}: banned word/phrase '{m.group(0)}' "
                    f"(matches '{term}')"
                )

    if not problems:
        return 0

    rel_display = (Path("drafts") / rel).as_posix()
    msg = [
        f"BLOCKED by guard_drafts.py: {rel_display} breaks the email studio's hard rules.",
        *[f"  - {p}" for p in problems],
        "Fix: use only @example.com addresses and example.com links (CLAUDE.md rule 4), "
        "and replace banned words with calm, sensory language from brand/voice-guide.md "
        "(CLAUDE.md rule 2). The file has already been written, so edit it now to remove "
        "every item above.",
    ]
    print("\n".join(msg), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
