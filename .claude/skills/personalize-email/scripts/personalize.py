#!/usr/bin/env python3
"""Render per-subscriber preview files for a Kettlebird Tea email draft.

Usage (from the repo root):
    python .claude/skills/personalize-email/scripts/personalize.py drafts/<slug>
    python .claude/skills/personalize-email/scripts/personalize.py drafts/<slug> --per-segment 2
    python .claude/skills/personalize-email/scripts/personalize.py drafts/<slug> --email ada.bloom@example.com

Reads:  data/subscribers.csv, drafts/<slug>/email.html, email.txt, segments.json
Writes: drafts/<slug>/previews/<segment>-<local-part>.html / .txt

Stdlib only. Reads and writes local files; never touches the network and
never sends anything. Any address that isn't @example.com is refused and is
never printed: rows are reported by line number only.
"""
import argparse
import csv
import html
import json
import re
import sys
import textwrap
from pathlib import Path

SEGMENTS = ("new", "active", "vip", "lapsed")
SAFE_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@example\.com$", re.IGNORECASE)
ANY_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ANY_URL = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SAFE_URL = re.compile(r"^https?://example\.com(/|$|\?)", re.IGNORECASE)
MERGE_TAG = re.compile(r"\{\{\s*([a-z_]+)\s*(?:\|([^}]*))?\}\}")
BANNED = re.compile(
    r"delv|unlock|game.?changer|elevat|revolutionar|synerg|seamless|leverag|"
    r"supercharg|next.?level|must.?have|act now|limited time|miss(?:ing)? out|"
    r"best ever|guilt.?free|detox",
    re.IGNORECASE,
)
# Used only when a tag has no inline fallback AND the field is empty.
DEFAULT_FALLBACKS = {
    "first_name": "there",
    "name": "there",
    "favorite_tea": "your favorite tea",
}
WRAP = 78


class Abort(Exception):
    pass


def safe_email(value):
    return bool(SAFE_EMAIL.match((value or "").strip()))


def load_subscribers(csv_path):
    rows, refused = [], []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
            if not safe_email(row.get("email")):
                refused.append(line_no)  # never echo the address itself
                continue
            row["_line"] = line_no
            rows.append(row)
    return rows, refused


def field_values(row, preview_id):
    name = row.get("name", "")
    return {
        "first_name": name.split()[0] if name.split() else "",
        "name": name,
        "favorite_tea": row.get("favorite_tea", ""),
        "segment": row.get("segment", ""),
        "subscriber_id": preview_id,
    }


def merge(text, values, escape):
    unknown = []

    def sub(m):
        tag, fallback = m.group(1), m.group(2)
        if tag not in values:
            unknown.append(tag)
            return m.group(0)
        value = values[tag]
        if not value:
            value = fallback.strip() if fallback is not None else DEFAULT_FALLBACKS.get(tag, "")
        return html.escape(value, quote=True) if escape else value

    out = MERGE_TAG.sub(sub, text)
    if unknown:
        raise Abort(f"unknown merge tag(s): {sorted(set(unknown))}")
    return out


def insert_html_callout(doc, callout_html):
    # After the greeting paragraph: the first <p> containing "Hi ".
    m = re.search(r"(<p[^>]*>\s*Hi [^<]*</p>)", doc)
    if not m:
        raise Abort("could not find the greeting paragraph in email.html")
    style = re.search(r"<p([^>]*)>", m.group(1)).group(1)
    para = f"\n            <p{style}>{callout_html}</p>"
    return doc[: m.end()] + para + doc[m.end():]


def insert_text_callout(doc, callout_text):
    lines = doc.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("Hi "):
            wrapped = textwrap.wrap(callout_text, WRAP, break_long_words=False,
                                    break_on_hyphens=False)
            return "\n".join(lines[: i + 1] + [""] + wrapped + lines[i + 1:])
    raise Abort("could not find the greeting line in email.txt")


def safety_scan(label, text):
    problems = []
    for e in ANY_EMAIL.findall(text):
        if not safe_email(e):
            problems.append(f"{label}: non-example.com email address")
    for u in ANY_URL.findall(text):
        if not SAFE_URL.match(u):
            problems.append(f"{label}: non-example.com URL")
    return problems


def check_output(label, text):
    problems = safety_scan(label, text)
    if MERGE_TAG.search(text) or "{{" in text:
        problems.append(f"{label}: unresolved merge tag")
    for i, line in enumerate(text.split("\n"), 1):
        if BANNED.search(line):
            problems.append(f"{label}:{i}: banned word '{BANNED.search(line).group(0)}'")
        if label.endswith(".txt") and len(line) > WRAP:
            problems.append(f"{label}:{i}: line over {WRAP} chars")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft", help="drafts/<slug>")
    ap.add_argument("--csv", default="data/subscribers.csv")
    ap.add_argument("--per-segment", type=int, default=1)
    ap.add_argument("--email", action="append", default=[],
                    help="render only this subscriber (repeatable)")
    args = ap.parse_args()

    draft = Path(args.draft)
    html_src = (draft / "email.html").read_text(encoding="utf-8")
    txt_src = (draft / "email.txt").read_text(encoding="utf-8")
    seg_path = draft / "segments.json"
    if not seg_path.exists():
        raise Abort(f"{seg_path} is missing: write the segment callouts first")
    callouts = json.loads(seg_path.read_text(encoding="utf-8"))
    for seg in SEGMENTS:
        if seg not in callouts:
            raise Abort(f"segments.json has no entry for '{seg}' (use \"\" for none)")

    # The source draft itself must already be clean.
    problems = safety_scan("email.html", html_src) + safety_scan("email.txt", txt_src)
    for seg, text in callouts.items():
        problems += safety_scan(f"segments.json[{seg}]", text)
        if BANNED.search(text):
            problems.append(f"segments.json[{seg}]: banned word '{BANNED.search(text).group(0)}'")
        if ANY_URL.search(text) or "<a" in text.lower():
            problems.append(f"segments.json[{seg}]: callouts may not add links (one CTA rule)")
    if problems:
        raise Abort("source check failed:\n  " + "\n  ".join(problems))

    for e in args.email:
        if not safe_email(e):
            raise Abort("refused: --email must be an @example.com address")

    rows, refused = load_subscribers(args.csv)
    if refused:
        print(f"REFUSED {len(refused)} row(s) with a non-@example.com address "
              f"(csv line {', '.join(map(str, refused))}); not processed.")

    if args.email:
        wanted = {e.lower() for e in args.email}
        picked = [r for r in rows if r["email"].lower() in wanted]
        missing = wanted - {r["email"].lower() for r in picked}
        if missing:
            raise Abort(f"not found in {args.csv}: {sorted(missing)}")
    else:
        picked = []
        for seg in SEGMENTS:
            seg_rows = [r for r in rows if r.get("segment") == seg][: args.per_segment]
            if not seg_rows:
                print(f"WARN no subscribers in segment '{seg}'")
            picked += seg_rows

    out_dir = draft / "previews"
    out_dir.mkdir(exist_ok=True)
    all_problems, written = [], []
    for row in picked:
        seg = row.get("segment", "")
        if seg not in SEGMENTS:
            all_problems.append(f"csv line {row['_line']}: unknown segment '{seg}'")
            continue
        local = row["email"].split("@")[0].lower()
        preview_id = f"preview-{seg}-{row['_line']}"
        values = field_values(row, preview_id)
        callout = callouts[seg].strip()

        h = merge(html_src, values, escape=True)
        t = merge(txt_src, values, escape=False)
        if callout:
            h = insert_html_callout(h, merge(callout, values, escape=True))
            t = insert_text_callout(t, merge(callout, values, escape=False))
        note = (f"PREVIEW ONLY, not for sending. segment={seg}; "
                f"to={row['email']}; source=drafts/{draft.name}")
        h = h.replace("<!DOCTYPE html>", f"<!DOCTYPE html>\n<!-- {note} -->", 1)
        t = f"[{note}]\n\n" + t
        # The note line may run past 78 chars; check the body only.
        body_t = t.split("\n", 2)[2]

        name = f"{seg}-{local}"
        all_problems += check_output(f"{name}.html", h)
        all_problems += check_output(f"{name}.txt", body_t)
        (out_dir / f"{name}.html").write_text(h, encoding="utf-8")
        (out_dir / f"{name}.txt").write_text(t, encoding="utf-8")
        written.append((seg, row["email"], name))

    for seg, email, name in written:
        print(f"WROTE {seg:<7} {email:<28} previews/{name}.html + .txt")
    if all_problems:
        print("FAIL\n  " + "\n  ".join(all_problems))
        return 1
    print(f"PASS {len(written)} preview pair(s): example.com only, no unresolved "
          f"tags, no banned words, txt lines <= {WRAP}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Abort as e:
        print(f"ABORT {e}")
        sys.exit(2)
