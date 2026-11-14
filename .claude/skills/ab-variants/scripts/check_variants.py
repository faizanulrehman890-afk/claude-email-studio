#!/usr/bin/env python3
"""Mechanical checks for drafts/<slug>/ab-variants.md (Kettlebird Tea A/B variants).

Usage (from the repo root):
    python .claude/skills/ab-variants/scripts/check_variants.py drafts/<slug>

Reads only local files. Never sends anything, never touches the network.
Prints one line per check (PASS / FAIL / WARN) and exits 1 if any check FAILs.

What it checks, for each of Variant A, B and C:
  * subject line <= 50 characters, preview text 40-90 characters
  * no banned words (list read from brand/voice-guide.md, plus other forms)
  * no ALL CAPS words, at most one '!' across the whole email it would ship in
  * no merge tags in subject/preview (so the character counts are real)
  * at most one emoji in the subject, links/addresses only on example.com
  * opening hook is 1-3 sentences and <= 50 words
  * subjects differ from each other and from the control
  * the comparison table's character counts match the real counts
Voice, facts and the segment hypotheses still need a read; see SKILL.md.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[4]
SUBJECT_MAX = 50
PREVIEW_MIN, PREVIEW_MAX = 40, 90
HOOK_MAX_WORDS = 50
HOOK_MAX_SENTENCES = 3
VARIANTS = ("A", "B", "C")
CAPS_OK = {"USA", "OR", "OK"}  # abbreviations, not shouting

# Always checked in addition to the voice guide's list (catches other forms).
EXTRA_BANNED = ["limited time", "miss out", "next level", "must have", "game changer"]
FALLBACK_BANNED = [
    "delve", "unlock", "game-changer", "elevate", "revolutionary", "synergy",
    "seamless", "leverage", "supercharge", "next-level", "must-have", "act now",
    "limited time only", "don't miss out", "best ever", "guilt-free", "detox",
]

EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF☀-➿\U0001F000-\U0001F2FF]")
URL_RE = re.compile(r"(?:https?://|www\.)([A-Za-z0-9.-]+)", re.I)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")
FIELD_RE = re.compile(r"^\s*-\s*\*\*(Subject|Preview|Opening hook):\*\*\s*(.+?)\s*$", re.M)
SECTION_RE = re.compile(r"^##\s+Variant\s+([A-Z])\b.*$", re.M)

results: list[tuple[str, str, str]] = []


def report(status: str, check: str, detail: str = "") -> None:
    results.append((status, check, detail))


def load_banned() -> list[str]:
    try:
        text = (ROOT / "brand" / "voice-guide.md").read_text(encoding="utf-8")
    except OSError:
        return FALLBACK_BANNED + EXTRA_BANNED
    m = re.search(r"^##\s+Banned words and phrases\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return FALLBACK_BANNED + EXTRA_BANNED
    terms = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        item = re.sub(r"\(.*?\)", "", line[2:])
        for part in item.split("/"):
            term = part.strip().strip('"“”').strip()
            if term:
                terms.append(term.lower())
    return list(dict.fromkeys((terms or FALLBACK_BANNED) + EXTRA_BANNED))


def term_pattern(term: str) -> re.Pattern[str]:
    """Case-insensitive, hyphen/space tolerant, and catches other word forms."""
    words = re.split(r"[\s\-]+", term.replace("’", "'"))
    parts = [re.escape(w).replace("'", "['’]") for w in words]
    if len(parts) == 1:
        stem = parts[0]
        if len(stem) > 4 and stem.endswith("e"):
            stem = stem[:-1]  # elevate -> elevat(ed|ing|ion)
        body = stem + r"\w*"
    else:
        body = r"[\s\-]+".join(parts)
    return re.compile(r"(?<!\w)" + body + r"(?!\w)", re.I)


def email_body_bangs(slug_dir: Path) -> int:
    """'!' in email.txt outside the Subject/Preview lines (those are what we replace)."""
    try:
        lines = (slug_dir / "email.txt").read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0
    return sum(l.count("!") for l in lines if not l.startswith(("Subject:", "Preview:")))


def control_subject(slug_dir: Path) -> str:
    try:
        for l in (slug_dir / "email.txt").read_text(encoding="utf-8").splitlines():
            if l.startswith("Subject:"):
                return l[len("Subject:"):].strip()
    except OSError:
        pass
    return ""


def parse_variants(text: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    heads = list(SECTION_RE.finditer(text))
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        nxt = re.search(r"^##\s", text[h.end():end], re.M)
        block = text[h.end(): h.end() + nxt.start()] if nxt else text[h.end():end]
        fields = {k.lower(): v for k, v in FIELD_RE.findall(block)}
        out[h.group(1)] = fields
    return out


def strip_md(s: str) -> str:
    """Field values may be wrapped in backticks or quotes for display."""
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "`\"":
        s = s[1:-1]
    return s


def parse_table(text: str) -> dict[str, dict[str, str]]:
    rows = [l for l in text.splitlines() if l.strip().startswith("|")]
    if len(rows) < 2:
        return {}
    header = [c.strip().lower() for c in rows[0].strip().strip("|").split("|")]
    out = {}
    for r in rows[2:]:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        if len(cells) != len(header):
            continue
        key = re.sub(r"[*`]", "", cells[0]).strip()
        out[key] = dict(zip(header, cells))
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    slug_dir = Path(sys.argv[1])
    if not slug_dir.is_absolute():
        slug_dir = (Path.cwd() / slug_dir).resolve()
    path = slug_dir / "ab-variants.md"
    if not path.exists():
        print(f"FAIL  File present: {path} not found")
        return 1
    text = path.read_text(encoding="utf-8")

    variants = parse_variants(text)
    missing = [v for v in VARIANTS if v not in variants]
    report("FAIL" if missing else "PASS", "Variants A, B, C present",
           f"missing: {', '.join(missing)}" if missing else "all three sections found")

    banned = [(t, term_pattern(t)) for t in load_banned()]
    body_bangs = email_body_bangs(slug_dir)
    control = control_subject(slug_dir)
    computed: dict[str, tuple[int, int]] = {}

    for v in VARIANTS:
        f = variants.get(v, {})
        subj, prev, hook = (strip_md(f.get(k, "")) for k in ("subject", "preview", "opening hook"))
        name = f"Variant {v}"
        if not (subj and prev and hook):
            report("FAIL", f"{name}: fields", "needs **Subject:**, **Preview:** and **Opening hook:** lines")
            continue
        computed[v] = (len(subj), len(prev))

        report("PASS" if len(subj) <= SUBJECT_MAX else "FAIL", f"{name}: subject length",
               f"{len(subj)} chars (max {SUBJECT_MAX})")
        report("PASS" if PREVIEW_MIN <= len(prev) <= PREVIEW_MAX else "FAIL", f"{name}: preview length",
               f"{len(prev)} chars ({PREVIEW_MIN}-{PREVIEW_MAX})")

        all_copy = " ".join((subj, prev, hook))
        hits = sorted({f"'{m.group(0)}' (~{t})" for t, p in banned for m in p.finditer(all_copy)})
        report("FAIL" if hits else "PASS", f"{name}: banned words", "; ".join(hits) or f"0 hits ({len(banned)} terms)")

        caps = [w for w in re.findall(r"\b[A-Z]{2,}\b", all_copy) if w not in CAPS_OK]
        report("FAIL" if caps else "PASS", f"{name}: no ALL CAPS", ", ".join(caps) or "none")

        bangs = all_copy.count("!")
        total = bangs + body_bangs
        report("FAIL" if total > 1 else ("WARN" if bangs else "PASS"), f"{name}: at most one '!'",
               f"{bangs} in variant + {body_bangs} in email body = {total}")

        tags = re.findall(r"\{\{.*?\}\}", subj + " " + prev)
        report("FAIL" if tags else "PASS", f"{name}: no merge tags in subject/preview",
               ", ".join(tags) or "none")

        emojis = EMOJI_RE.findall(subj)
        report("FAIL" if len(emojis) > 1 else ("WARN" if emojis else "PASS"), f"{name}: emoji",
               f"{len(emojis)} in subject (max 1, prefer none)")

        bad_links = [h for h in URL_RE.findall(all_copy) if not re.fullmatch(r"(?:[\w-]+\.)*example\.com", h, re.I)]
        bad_mail = [d for d in EMAIL_RE.findall(all_copy) if d.lower() != "example.com"]
        report("FAIL" if bad_links or bad_mail else "PASS", f"{name}: example.com only",
               ", ".join(bad_links + bad_mail) or "no other domains")

        words = len(hook.split())
        sentences = len([s for s in re.split(r"(?<=[.?!])\s+", hook) if s.strip()])
        ok = words <= HOOK_MAX_WORDS and 1 <= sentences <= HOOK_MAX_SENTENCES
        report("PASS" if ok else "FAIL", f"{name}: hook size",
               f"{sentences} sentence(s), {words} words (max {HOOK_MAX_SENTENCES} / {HOOK_MAX_WORDS})")

        if prev.lower().startswith(subj.lower()[:20]):
            report("WARN", f"{name}: preview adds something", "preview opens like the subject")

    subjects = [strip_md(variants.get(v, {}).get("subject", "")).lower() for v in VARIANTS]
    dupes = len(set(subjects)) != len(subjects) or (control and control.lower() in subjects)
    report("FAIL" if dupes else "PASS", "Subjects distinct",
           "a subject repeats another variant or the control" if dupes else "A, B, C and control all differ")

    table = parse_table(text[text.find("## Comparison"):] if "## Comparison" in text else "")
    if not table:
        report("FAIL", "Comparison table", "no table under '## Comparison'")
    else:
        need = {"angle", "subject chars", "preview chars", "best-fit segment", "hypothesis"}
        cols = set(next(iter(table.values())).keys())
        report("FAIL" if need - cols else "PASS", "Comparison table columns",
               f"missing: {', '.join(sorted(need - cols))}" if need - cols else "all present")
        wrong = []
        for v, (s, p) in computed.items():
            row = table.get(v) or table.get(f"Variant {v}")
            if not row:
                wrong.append(f"{v}: no row")
                continue
            if row.get("subject chars", "").strip() != str(s):
                wrong.append(f"{v} subject says {row.get('subject chars')}, real {s}")
            if row.get("preview chars", "").strip() != str(p):
                wrong.append(f"{v} preview says {row.get('preview chars')}, real {p}")
        report("FAIL" if wrong else "PASS", "Table counts match real counts", "; ".join(wrong) or "all match")

    for status, check, detail in results:
        print(f"{status:<5} {check}: {detail}")
    fails = sum(1 for r in results if r[0] == "FAIL")
    warns = sum(1 for r in results if r[0] == "WARN")
    print(f"\n{'FAIL' if fails else 'PASS'}: {fails} fail, {warns} warn, {len(results)} checks")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
