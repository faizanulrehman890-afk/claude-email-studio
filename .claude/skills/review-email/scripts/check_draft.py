#!/usr/bin/env python3
"""Mechanical QA checks for an email draft in drafts/<slug>/.

Brand-aware: the default brand is Kettlebird Tea (brand/ + CLAUDE.md). A draft
with drafts/<slug>/brand.txt (e.g. "rise-and-crumb") is checked against
brands/<brand>/ instead: its footer address, reason line and extra banned
words. The CLAUDE.md hard rules (example.com only, one CTA, full footer, house
banned words) apply to every brand. See scripts/brand_profile.py.

Usage (from the repo root):
    python .claude/skills/review-email/scripts/check_draft.py drafts/<slug>

Reads only local files. Never sends anything, never touches the network.
Prints one line per check: PASS / FAIL / WARN, with file:line for issues.
Exit code 1 if any check FAILs, else 0.

This covers the checks a script can do reliably. Voice, tone and fact
accuracy still need a human (or Claude) read; see SKILL.md.
"""
import csv
import difflib
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
from brand_profile import fs_reader, brand_of_draft, load_profile  # noqa: E402

BANNED = re.compile(
    r"delv\w*|unlock\w*|game[\s-]?changer\w*|elevat\w*|revolutionar\w*|synerg\w*|"
    r"seamless\w*|leverag\w*|supercharg\w*|next[\s-]?level|must[\s-]?have\w*|"
    r"act now|limited time|miss out|best ever|guilt[\s-]?free|detox\w*",
    re.I,
)
# Words allowed in capitals (abbreviations, not shouting).
CAPS_OK = {"USA", "OR", "DOCTYPE", "UTM", "CTA"}
URL_RE = re.compile(r"""https?://[^\s"'<>)]+""", re.I)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
TAG_RE = re.compile(r"\{\{\s*([a-zA-Z_]+)")
UNSUB = "https://example.com/unsubscribe?id="
PREFS = "https://example.com/preferences?id="


def term_pattern(term):
    """Case-insensitive; also catches other forms (magical, unlocks, elevated)."""
    words = re.split(r"[\s\-]+", term.replace("’", "'"))
    parts = [re.escape(w).replace("'", "['’]") for w in words]
    if len(parts) == 1:
        stem = parts[0]
        if len(stem) > 4 and stem.endswith("e"):
            stem = stem[:-1]  # elevate -> elevat(e|ed|ing)
        body = stem + r"\w*"
    else:
        body = r"[\s\-]+".join(parts)
    return re.compile(r"(?<![\w])" + body + r"(?![\w])", re.I)

results = []  # (status, check, detail)


def report(status, check, detail=""):
    results.append((status, check, detail))


def lines_of(path):
    return path.read_text(encoding="utf-8").splitlines()


class Visible(HTMLParser):
    """Collect visible body text with line numbers; skip <head> and hidden divs."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks = []  # (line, text)
        self.skip = 0
        self.stack = []
        self.imgs = []  # (line, attrs)
        self.links = []  # (line, href, text)
        self._a = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        style = (a.get("style") or "").replace(" ", "").lower()
        hidden = tag in ("head", "style", "title", "script") or "display:none" in style
        if tag not in ("br", "img", "meta", "link", "hr", "input"):
            self.stack.append(hidden)
            if hidden:
                self.skip += 1
        if tag == "img":
            self.imgs.append((self.getpos()[0], a))
        if tag == "a":
            self._a = [self.getpos()[0], a.get("href", ""), ""]
        if tag in ("br", "p", "li", "td", "div"):
            self.chunks.append((self.getpos()[0], "\n"))

    def handle_endtag(self, tag):
        if tag == "a" and self._a:
            self.links.append(tuple(self._a))
            self._a = None
        if tag in ("br", "img", "meta", "link", "hr", "input"):
            return
        if self.stack and self.stack.pop():
            self.skip -= 1

    def handle_data(self, data):
        if self.skip:
            return
        self.chunks.append((self.getpos()[0], data))
        if self._a is not None:
            self._a[2] += data


def words(text):
    text = text.replace(" ", " ")
    return re.findall(r"[A-Za-z0-9$°{}|_']+", text.lower())


def main(folder):
    d = Path(folder)
    h_path, t_path = d / "email.html", d / "email.txt"
    for p in (h_path, t_path):
        if not p.exists():
            report("FAIL", "Files present", f"missing {p}")
    if any(r[0] == "FAIL" for r in results):
        return finish()
    report("PASS", "Files present", "email.html + email.txt")

    hl, tl = lines_of(h_path), lines_of(t_path)
    h_raw = h_path.read_text(encoding="utf-8")
    both = [(h_path, hl), (t_path, tl)]

    # Brand profile: address from CLAUDE.md (default brand) or from
    # brands/<brand>/products.md, never from an older draft.
    read = fs_reader(Path.cwd())
    try:
        brand = brand_of_draft(d.as_posix(), read)
    except ValueError as exc:
        report("FAIL", "Brand profile", str(exc))
        return finish()
    prof = load_profile(brand, read)
    address, reason = prof["address"], prof["reason"]
    report("FAIL" if prof["errors"] else "PASS", "Brand profile",
           "; ".join(prof["errors"]) or
           f"{prof['name']} ({brand}): {prof['voice_guide']}, {prof['products']}")
    caps_ok = CAPS_OK | set(re.findall(r"\b[A-Z]{2,}\b", address or ""))

    # --- Banned words (house list + brand list) ------------------------------
    pats = [BANNED] + [term_pattern(t) for t in prof["banned"]]
    hits = sorted({f"{p.name}:{i}: '{mm.group(0)}'" for p, ls in both
                   for i, l in enumerate(ls, 1) for pat in pats
                   for mm in pat.finditer(html.unescape(l))})
    report("FAIL" if hits else "PASS", "Banned words (case-insensitive)",
           "; ".join(hits) or "0 hits in both files")

    # --- Shouting: ALL CAPS and exclamation marks (visible text) -------------
    v = Visible()
    v.feed(h_raw)
    vis_lines = {}
    for ln, txt in v.chunks:
        vis_lines.setdefault(ln, []).append(txt)
    caps = [f"email.html:{ln}: {w}" for ln, ts in vis_lines.items()
            for w in re.findall(r"\b[A-Z]{2,}\b", " ".join(ts)) if w not in caps_ok]
    caps += [f"email.txt:{i}: {w}" for i, l in enumerate(tl, 1)
             for w in re.findall(r"\b[A-Z]{2,}\b", l) if w not in caps_ok]
    for i, l in enumerate(hl, 1):  # <title> and preheader live outside visible text
        for seg in re.findall(r"<title>(.*?)</title>|display:\s*none[^>]*>([^<]*)", l):
            caps += [f"email.html:{i}: {w}" for w in re.findall(r"\b[A-Z]{2,}\b", " ".join(seg)) if w not in caps_ok]
    report("FAIL" if caps else "PASS", "No ALL CAPS words", "; ".join(caps) or
           f"none ({'/'.join(sorted(caps_ok - {'DOCTYPE', 'UTM', 'CTA'}))} allowed)")
    bangs = {}
    for p, ls in both:
        for i, l in enumerate(ls, 1):
            n = l.replace("<!DOCTYPE", "").replace("!important", "").count("!")
            bangs.setdefault(p.name, []).extend([i] * n)
    bad = {k: x for k, x in bangs.items() if len(x) > 1}
    report("FAIL" if bad else "PASS", "At most one '!' per email",
           "; ".join(f"{k}: {len(x)} on lines {sorted(set(x))}" for k, x in bad.items()) or
           ", ".join(f"{k}: {len(x)}" for k, x in bangs.items()))

    # --- Subject & preview ---------------------------------------------------
    subj = next((l[8:].strip() for l in tl if l.startswith("Subject:")), None)
    prev = next((l[8:].strip() for l in tl if l.startswith("Preview:")), None)
    tm = re.search(r"<title>(.*?)</title>", h_raw, re.S)
    title = html.unescape(tm.group(1).strip()) if tm else None
    pm = re.search(r"<div[^>]*display:\s*none[^>]*>(.*?)</div>", h_raw, re.S)
    pre = html.unescape(re.sub(r"<[^>]+>", "", pm.group(1))).replace("‌", "").strip() if pm else None
    if subj is None or title is None:
        report("FAIL", "Subject line", f"Subject: line {'found' if subj else 'missing'} in txt; <title> {'found' if title else 'missing'} in html")
    else:
        ok = len(subj) <= 50 and subj == title
        report("PASS" if ok else "FAIL", "Subject <= 50 chars, same in both",
               f"'{subj}' = {len(subj)} chars" + ("" if subj == title else f"; html <title> differs: '{title}'"))
    if prev is None or pre is None:
        report("FAIL", "Preview text", f"Preview: line {'found' if prev else 'missing'} in txt; hidden preheader {'found' if pre else 'missing'} in html")
    else:
        ok = 40 <= len(prev) <= 90 and prev == pre
        report("PASS" if ok else "FAIL", "Preview 40-90 chars, same in both",
               f"{len(prev)} chars" + ("" if prev == pre else f"; html preheader differs: '{pre}'"))

    # --- Single CTA ----------------------------------------------------------
    is_footer = lambda u: u.startswith(UNSUB) or u.startswith(PREFS)
    h_cta = [(ln, href, txt.strip()) for ln, href, txt in v.links if not is_footer(href)]
    t_cta = [(i, u) for i, l in enumerate(tl, 1) for u in URL_RE.findall(l) if not is_footer(u)]
    ok = len(h_cta) == 1 and len(t_cta) == 1 and html.unescape(h_cta[0][1]) == t_cta[0][1]
    report("PASS" if ok else "FAIL", "Exactly one CTA, same URL in both",
           "; ".join(f"email.html:{ln} '{t}' -> {u}" for ln, u, t in h_cta) + " | " +
           "; ".join(f"email.txt:{i} {u}" for i, u in t_cta))

    # --- Footer --------------------------------------------------------------
    for p, ls in both:
        text = "\n".join(ls)
        plain = html.unescape(text) if p.suffix == ".html" else text
        missing = []
        if not address or address not in plain:
            missing.append(f"exact address '{address}'")
        if not reason or reason not in plain:
            missing.append("reason line")
        if UNSUB not in plain:
            missing.append("unsubscribe link")
        if PREFS not in plain:
            missing.append("preferences link")
        line = next((i for i, l in enumerate(ls, 1) if address and address in html.unescape(l)), "-")
        report("FAIL" if missing else "PASS", f"Footer ({p.name})",
               ("missing: " + ", ".join(missing)) if missing else f"address at line {line}, reason, unsubscribe, preferences")

    # --- Safe links & addresses ---------------------------------------------
    bad = []
    for p, ls in both:
        for i, l in enumerate(ls, 1):
            for u in URL_RE.findall(l):
                if not re.match(r"https?://example\.com(/|$|\?)", u, re.I):
                    bad.append(f"{p.name}:{i}: {u}")
            for e in EMAIL_RE.findall(l):
                if not e.lower().endswith("@example.com"):
                    bad.append(f"{p.name}:{i}: {e}")
            for attr in re.findall(r'(?:href|src)="([^"]*)"', l):
                if attr and not attr.lower().startswith(("https://example.com", "http://example.com", "mailto:")):
                    bad.append(f"{p.name}:{i}: {attr}")
                if attr.lower().startswith("mailto:") and not attr.lower().endswith("@example.com"):
                    bad.append(f"{p.name}:{i}: {attr}")
            if re.search(r"\bwww\.(?!example\.com)", l, re.I):
                bad.append(f"{p.name}:{i}: bare www. domain")
    bad = list(dict.fromkeys(html.unescape(b) for b in bad))
    report("FAIL" if bad else "PASS", "Only example.com links / @example.com addresses",
           "; ".join(bad) or "all URLs and addresses on example.com")

    # --- HTML technical ------------------------------------------------------
    issues = []
    if not re.search(r'<meta[^>]+name="viewport"', h_raw):
        issues.append("no viewport meta")
    for i, l in enumerate(hl, 1):
        for w in re.findall(r'\bwidth="(\d+)"', l):
            if int(w) > 600:
                issues.append(f"line {i}: width=\"{w}\"")
        if "@media" in l:  # breakpoints aren't element widths
            continue
        for w in re.findall(r"(?<![-\w])(?:max-|min-)?width:\s*(\d+)px", l):
            if int(w) > 600:
                issues.append(f"line {i}: width {w}px")
        if re.search(r"<(script|form|video|iframe)\b|<link[^>]+stylesheet", l, re.I):
            issues.append(f"line {i}: disallowed tag")
    if 'max-width:600px' not in h_raw.replace(" ", ""):
        issues.append("no max-width:600px container")
    report("FAIL" if issues else "PASS", "Mobile single-column HTML (<= 600px)",
           "; ".join(issues) or "viewport meta, 600px container, no wide elements, no script/forms")
    alt_bad = [f"line {ln}" + (" (no alt)" if "alt" not in a else "") + (" (no width)" if "width" not in a else "")
               for ln, a in v.imgs if "alt" not in a or "width" not in a]
    report("FAIL" if alt_bad else "PASS", "Images have alt + width",
           "; ".join(alt_bad) or (f"{len(v.imgs)} image(s), all OK" if v.imgs else "no images"))
    small = [f"line {i}: {s}px" for i, l in enumerate(hl, 1)
             for s in re.findall(r"font-size:\s*(\d+)px", l) if int(s) < 16]
    report("WARN" if small else "PASS", "Body text >= 16px",
           ("under 16px (OK only for footer/brand label): " + "; ".join(small)) if small else "all >= 16px")

    # --- Plain-text hygiene & parity ----------------------------------------
    long_ = [f"line {i} ({len(l)} chars)" for i, l in enumerate(tl, 1) if len(l) > 78]
    markup = [f"line {i}" for i, l in enumerate(tl, 1)
              if re.search(r"<[a-z/][^>]*>|\*\*|__|\[[^\]]+\]\(|&[a-z]+;", l, re.I)]
    report("FAIL" if long_ else "PASS", "Plain-text lines <= 78 chars", "; ".join(long_) or "all lines fit")
    report("FAIL" if markup else "PASS", "Plain text has no HTML/markdown", "; ".join(markup) or "clean")

    body_t = [l for l in tl if not l.startswith(("Subject:", "Preview:")) and l.strip() != "---"]
    tw = words(URL_RE.sub(" ", "\n".join(body_t)))
    hw = words("".join(t for _, t in v.chunks))
    diff = [x for x in difflib.ndiff(hw, tw) if x[:2] in ("- ", "+ ")]
    if diff:
        sm = difflib.SequenceMatcher(None, hw, tw)
        parts = []
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op != "equal":
                parts.append(f"{op}: html '{' '.join(hw[a1:a2])}' vs txt '{' '.join(tw[b1:b2])}'")
        report("FAIL", "Parity: txt copy matches html copy", "; ".join(parts[:8]))
    else:
        report("PASS", "Parity: txt copy matches html copy", f"{len(hw)} words, identical order")

    # --- Merge tags vs sample data (advisory) -------------------------------
    tags = sorted({t for _, ls in both for l in ls for t in TAG_RE.findall(l)})
    csv_path = Path("data/subscribers.csv")
    if tags and csv_path.exists():
        with csv_path.open(encoding="utf-8") as f:
            cols = set(next(csv.reader(f)))
        missing = [t for t in tags if t not in cols]
        report("WARN" if missing else "PASS", "Merge tags exist in data/subscribers.csv",
               (f"not columns in the sample CSV: {missing} (columns: {sorted(cols)}); "
                "fine if the email platform supplies them, but they can't be tested with this CSV")
               if missing else f"all of {tags} present")

    return finish()


def finish():
    w = max(len(c) for _, c, _ in results) if results else 10
    for s, c, dtl in results:
        print(f"{s:<4}  {c:<{w}}  {dtl}")
    fails = sum(1 for s, _, _ in results if s == "FAIL")
    warns = sum(1 for s, _, _ in results if s == "WARN")
    print(f"\n{len(results)} checks: {fails} FAIL, {warns} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: check_draft.py drafts/<slug>")
    sys.exit(main(sys.argv[1]))
