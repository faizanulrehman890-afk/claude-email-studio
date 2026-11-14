#!/usr/bin/env python3
"""Git pre-commit audit for the Kettlebird email studio (stdlib only).

Checks every staged file (added, copied or modified) against the repo's
hard rules, reading the *staged* content (the index), not the working tree:

  1. Emails:  any address not @example.com, in any staged file.
  2. Links:   any URL whose host is not example.com (or a subdomain),
              in files under drafts/ or data/.
  3. Banned:  banned words/phrases from brand/voice-guide.md, in email copy:
              drafts/*/email.html, drafts/*/email.txt, drafts/*/previews/*,
              drafts/*/ab-variants.md.
  4. Secrets: .env files, private-key files, and content that looks like an
              API key or private key.

Exit 0 = clean, exit 1 = commit blocked (findings printed to stderr).

Usage:
  python scripts/pre_commit_audit.py          # audit staged files (hook mode)
  python scripts/pre_commit_audit.py --all    # audit every tracked file
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
from pathlib import PurePosixPath

try:
    sys.stderr.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ALLOWED_DOMAIN = "example.com"
VOICE_GUIDE = "brand/voice-guide.md"
URL_SCOPES = ("drafts/", "data/")
COPY_GLOBS = (
    "drafts/*/email.html",
    "drafts/*/email.txt",
    "drafts/*/previews/*",
    "drafts/*/ab-variants.md",
)
FALLBACK_BANNED = [
    "delve", "unlock", "game-changer", "game changer", "elevate", "revolutionary",
    "synergy", "seamless", "leverage", "supercharge", "next-level", "must-have",
    "act now", "limited time only", "don't miss out", "best ever", "guilt-free",
    "detox",
]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@([A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+)")
URL_RE = re.compile(
    r"(?:\b(?:https?|ftp)://|(?<![\w/@.])//|\bwww\.)([A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+)",
    re.IGNORECASE,
)

# Filenames that are secrets by nature. ".env.example" / ".env.sample" are allowed.
SECRET_NAME_GLOBS = ("*.env", ".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx",
                     "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519")
SECRET_NAME_ALLOW = (".env.example", ".env.sample", ".env.template")
SECRET_CONTENT = [
    ("OpenAI/Anthropic-style key (sk-...)", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_\-]{20,}")),
    ("Resend-style key (re_...)", re.compile(r"\bre_[A-Za-z0-9]{8,}_[A-Za-z0-9_]{8,}|\bre_[A-Za-z0-9]{24,}")),
    ("SendGrid key (SG.)", re.compile(r"\bSG\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,}")),
    ("AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("Private key block", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
    ("Hard-coded API key/secret assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password)\b"
        r"\s*[:=]\s*['\"][A-Za-z0-9_\-./+=]{16,}['\"]")),
]


# ---------------------------------------------------------------- git helpers
def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def staged_files() -> list[str]:
    out = git("diff", "--cached", "--name-only", "--diff-filter=ACM", "-z")
    return [p for p in out.decode("utf-8").split("\0") if p]


def tracked_files() -> list[str]:
    return [p for p in git("ls-files", "-z").decode("utf-8").split("\0") if p]


def read_blob(path: str, from_index: bool) -> str | None:
    """Return text content (staged version in hook mode), or None for binaries."""
    try:
        data = git("show", f":{path}") if from_index else open(path, "rb").read()
    except (subprocess.CalledProcessError, OSError):
        return None
    if b"\0" in data[:8000]:
        return None
    return data.decode("utf-8", errors="replace")


# ------------------------------------------------------------- banned words
def load_banned(from_index: bool) -> list[str]:
    text = read_blob(VOICE_GUIDE, from_index) or read_blob(VOICE_GUIDE, False)
    if not text:
        return FALLBACK_BANNED
    m = re.search(r"^##\s+Banned words and phrases\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return FALLBACK_BANNED
    terms: list[str] = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        item = re.sub(r"\(.*?\)", "", line[2:])        # drop "(we make no health claims)"
        for part in item.split("/"):                   # "game-changer / game changer"
            term = part.strip().strip('"“”').strip()
            if term:
                terms.append(term.lower())
    return list(dict.fromkeys(terms)) or FALLBACK_BANNED


def term_pattern(term: str) -> re.Pattern[str]:
    """Case-insensitive; also catches other forms (unlocks, elevated, leveraging)."""
    words = re.split(r"[\s\-]+", term.replace("’", "'"))
    parts = [re.escape(w).replace("'", "['’]") for w in words]
    if len(parts) == 1:
        stem = parts[0]
        if len(stem) > 4 and stem.endswith("e"):
            stem = stem[:-1]
        body = stem + r"\w*"
    else:
        body = r"[\s\-]+".join(parts)
    return re.compile(r"(?<!\w)" + body + r"(?!\w)", re.IGNORECASE)


# ------------------------------------------------------------------ checks
def domain_ok(host: str) -> bool:
    host = host.lower().rstrip(".")
    return host == ALLOWED_DOMAIN or host.endswith("." + ALLOWED_DOMAIN)


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def is_copy(path: str) -> bool:
    return any(fnmatch.fnmatchcase(path, g) for g in COPY_GLOBS)


def is_secret_name(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    if name in SECRET_NAME_ALLOW:
        return False
    return any(fnmatch.fnmatchcase(name, g) for g in SECRET_NAME_GLOBS)


def audit(paths: list[str], from_index: bool) -> list[str]:
    problems: list[str] = []
    patterns = [(t, term_pattern(t)) for t in load_banned(from_index)]

    for path in paths:
        if is_secret_name(path):
            problems.append(f"{path}: secret-type file ({PurePosixPath(path).name}) must not be committed")
            continue

        text = read_blob(path, from_index)
        if text is None:
            continue

        for m in EMAIL_RE.finditer(text):
            if m.group(1).lower().rstrip(".") != ALLOWED_DOMAIN:
                problems.append(f"{path}:{line_of(text, m.start())}: email '{m.group(0)}' is not @{ALLOWED_DOMAIN}")

        if path.startswith(URL_SCOPES):
            for m in URL_RE.finditer(text):
                if not domain_ok(m.group(1)):
                    problems.append(f"{path}:{line_of(text, m.start())}: link to '{m.group(1)}' is not {ALLOWED_DOMAIN}")

        if is_copy(path):
            for term, pat in patterns:
                for m in pat.finditer(text):
                    problems.append(f"{path}:{line_of(text, m.start())}: banned word '{m.group(0)}' (matches '{term}')")

        for label, pat in SECRET_CONTENT:
            for m in pat.finditer(text):
                shown = m.group(0)[:8] + "…"
                problems.append(f"{path}:{line_of(text, m.start())}: looks like a secret: {label} ({shown})")

    return problems


def main(argv: list[str]) -> int:
    all_mode = "--all" in argv
    try:
        paths = tracked_files() if all_mode else staged_files()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"pre-commit audit: could not run git ({exc}); blocking to be safe.", file=sys.stderr)
        return 1

    problems = audit(paths, from_index=not all_mode)
    if not problems:
        print(f"pre-commit audit: {len(paths)} file(s) checked, all clean.")
        return 0

    print("COMMIT BLOCKED by scripts/pre_commit_audit.py:", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    print(
        "\nFix: only @example.com addresses and example.com links (CLAUDE.md rule 4); "
        "no banned words in email copy (rule 2, brand/voice-guide.md); "
        "no API keys or .env files (rule 7). Then re-stage and commit.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
