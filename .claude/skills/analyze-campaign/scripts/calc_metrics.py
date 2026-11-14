#!/usr/bin/env python3
"""calc_metrics.py: exact campaign metrics for the analyze-campaign skill.

Standard library only. Reads data/campaign-metrics.csv, validates every row for
one campaign, and prints a Markdown block (or JSON) with:

  * per row (segment x variant): Open Rate, CTR, CTOR, Unsubscribe Rate
  * the same rates rolled up by segment, by variant, and for the whole campaign
  * the winning segment/variant (highest CTR, sample-size and unsubscribe guardrails)
    and a two-proportion z-test of winner vs runner-up on CTR
  * optionally, a cross-check against the practice outbox (list_outbox JSON)

Formulas (all as percentages, rounded half-up to 2 decimal places):

    Open Rate   = opened_count       / sent_count   * 100
    CTR         = clicked_count      / sent_count   * 100
    CTOR        = clicked_count      / opened_count * 100
    Unsub Rate  = unsubscribed_count / sent_count   * 100

Rates are computed with fractions.Fraction (exact) and only rounded for display,
so roll-ups use summed counts, never averaged percentages.

Usage:
    python calc_metrics.py <campaign_slug>
        [--csv data/campaign-metrics.csv]
        [--subscribers data/subscribers.csv]
        [--drafts drafts]
        [--outbox-json PATH | -]     # saved output of the list_outbox MCP tool
        [--min-sent 100]             # rows below this can't win
        [--max-unsub 0.5]            # unsubscribe-rate guardrail, in percent
        [--format md|json]

Exit codes: 0 ok, 1 validation error (bad rows, slug not found), 2 usage error.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[4]
COLUMNS = [
    "campaign_slug", "segment", "variant", "sent_count",
    "opened_count", "clicked_count", "unsubscribed_count",
]
COUNT_COLS = COLUMNS[3:]
SEGMENTS = ("new", "active", "vip", "lapsed")  # CLAUDE.md audience segments
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VARIANT_RE = re.compile(r"^(control|[A-Z])$")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@([A-Za-z0-9\-.]+)")


# ----------------------------------------------------------------------- maths


def pct(num: int, den: int) -> Fraction | None:
    return None if den == 0 else Fraction(num * 100, den)


def fmt(value: Fraction | None, places: int = 2) -> str:
    if value is None:
        return "n/a"
    q = Decimal(value.numerator) / Decimal(value.denominator)
    return str(q.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def rates(c: dict) -> dict:
    return {
        "open_rate": pct(c["opened_count"], c["sent_count"]),
        "ctr": pct(c["clicked_count"], c["sent_count"]),
        "ctor": pct(c["clicked_count"], c["opened_count"]),
        "unsub_rate": pct(c["unsubscribed_count"], c["sent_count"]),
    }


def two_prop_z(c1: int, n1: int, c2: int, n2: int) -> tuple[float, float] | None:
    """Two-sided two-proportion z-test. Returns (z, p) or None if undefined."""
    if n1 == 0 or n2 == 0:
        return None
    p = (c1 + c2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return None
    z = (c1 / n1 - c2 / n2) / se
    return z, math.erfc(abs(z) / math.sqrt(2))


# ----------------------------------------------------------------------- input


def load_rows(csv_path: Path, slug: str) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    rows: list[dict] = []
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != COLUMNS:
            errors.append(f"header is {reader.fieldnames}, expected {COLUMNS}")
            return rows, errors
        seen: set[tuple[str, str]] = set()
        for lineno, raw in enumerate(reader, start=2):
            if any(EMAIL_RE.search(v or "") and not (v or "").lower().endswith("@example.com")
                   for v in raw.values()):
                errors.append(f"line {lineno}: non-@example.com address (CLAUDE.md rule 4)")
            if raw["campaign_slug"] != slug:
                continue
            where = f"line {lineno} ({raw['segment']}/{raw['variant']})"
            if raw["segment"] not in SEGMENTS:
                errors.append(f"{where}: unknown segment {raw['segment']!r}; use one of {SEGMENTS}")
            if not VARIANT_RE.fullmatch(raw["variant"] or ""):
                errors.append(f"{where}: variant must be 'control' or one capital letter")
            key = (raw["segment"], raw["variant"])
            if key in seen:
                errors.append(f"{where}: duplicate segment/variant row")
            seen.add(key)
            row = {"campaign_slug": slug, "segment": raw["segment"], "variant": raw["variant"],
                   "line": lineno}
            bad = False
            for col in COUNT_COLS:
                try:
                    n = int(raw[col])
                    if n < 0 or str(n) != raw[col].strip():
                        raise ValueError
                    row[col] = n
                except (TypeError, ValueError):
                    errors.append(f"{where}: {col}={raw[col]!r} is not a whole number >= 0")
                    bad = True
            if bad:
                continue
            if row["opened_count"] > row["sent_count"]:
                errors.append(f"{where}: opened_count > sent_count")
            if row["clicked_count"] > row["opened_count"]:
                errors.append(f"{where}: clicked_count > opened_count")
            if row["unsubscribed_count"] > row["sent_count"]:
                errors.append(f"{where}: unsubscribed_count > sent_count")
            if row["sent_count"] == 0:
                errors.append(f"{where}: sent_count is 0, rates are undefined")
            rows.append(row)
    if not rows and not errors:
        errors.append(f"no rows for campaign_slug {slug!r} in {csv_path.name}")
    return rows, errors


def rollup(rows: list[dict], key: str | None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in rows:
        k = "all" if key is None else r[key]
        agg = out.setdefault(k, {c: 0 for c in COUNT_COLS} | {"rows": 0})
        for c in COUNT_COLS:
            agg[c] += r[c]
        agg["rows"] += 1
    return out


def draft_subjects(drafts_dir: Path, slug: str) -> dict[str, str]:
    """Subject per variant: control from email.txt, A/B/C.. from ab-variants.md."""
    subjects: dict[str, str] = {}
    txt = drafts_dir / slug / "email.txt"
    if txt.is_file():
        for line in txt.read_text(encoding="utf-8").splitlines():
            if line.startswith("Subject:"):
                subjects["control"] = line.split(":", 1)[1].strip()
                break
    ab = drafts_dir / slug / "ab-variants.md"
    if ab.is_file():
        current = None
        for line in ab.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^## Variant ([A-Z])\b", line)
            if m:
                current = m.group(1)
            elif line.startswith("## "):
                current = None
            elif current and line.startswith("- **Subject:**"):
                subjects[current] = line.split("**Subject:**", 1)[1].strip()
    return subjects


def subscriber_segments(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    with path.open(newline="", encoding="utf-8") as fh:
        return {r["email"].strip().lower(): r["segment"].strip() for r in csv.DictReader(fh)}


def outbox_check(outbox_json: str, slug: str, rows: list[dict],
                 subs: dict[str, str], subjects: dict[str, str]) -> dict:
    text = sys.stdin.read() if outbox_json == "-" else Path(outbox_json).read_text(encoding="utf-8")
    data = json.loads(text)
    emails = [e for e in data.get("emails", []) if e.get("campaign_slug") == slug]
    sends = []
    for e in emails:
        to = (e.get("to") or "").lower()
        subj = e.get("subject", "")
        variant = next((v for v, s in subjects.items() if s == subj), None)
        sends.append({
            "to": to,
            "segment": subs.get(to, "unknown"),
            "subject": subj,
            "variant": variant or "unmatched",
            "example_com": to.endswith("@example.com"),
            "sent_at": e.get("sent_at", ""),
        })
    metric_pairs = {(r["segment"], r["variant"]) for r in rows}
    sent_pairs = {(s["segment"], s["variant"]) for s in sends}
    issues = []
    if not sends:
        issues.append(f"no practice sends for {slug!r} in the outbox")
    for seg, var in sorted(metric_pairs - sent_pairs):
        issues.append(f"metrics row {seg}/{var} has no matching practice send")
    for s in sends:
        if not s["example_com"]:
            issues.append(f"practice send to non-@example.com address {s['to']}")
        if s["variant"] == "unmatched":
            issues.append(f"practice send to {s['to']} has subject {s['subject']!r}, "
                          "which matches no draft/variant subject")
        if s["segment"] == "unknown":
            issues.append(f"practice send to {s['to']} is not in subscribers.csv")
    extra = sorted(p for p in sent_pairs - metric_pairs if "unknown" not in p and "unmatched" not in p)
    for seg, var in extra:
        issues.append(f"practice send exists for {seg}/{var} but there is no metrics row")
    return {"practice_sends": len(sends), "sends": sends, "issues": issues,
            "count_in_list": data.get("count")}


# ----------------------------------------------------------------------- report


def pick_winner(rows: list[dict], min_sent: int, max_unsub: Fraction) -> dict:
    eligible, excluded = [], []
    for r in rows:
        rt = rates(r)
        if r["sent_count"] < min_sent:
            excluded.append((r, f"sent_count {r['sent_count']} < min {min_sent}"))
        elif rt["unsub_rate"] is not None and rt["unsub_rate"] > max_unsub:
            excluded.append((r, f"unsub rate {fmt(rt['unsub_rate'])}% > guardrail {fmt(max_unsub)}%"))
        else:
            eligible.append(r)
    # Highest CTR; ties broken by CTOR, then lower unsubscribe rate, then larger sample.
    eligible.sort(key=lambda r: (rates(r)["ctr"], rates(r)["ctor"] or 0,
                                 -(rates(r)["unsub_rate"] or 0), r["sent_count"]), reverse=True)
    result = {"winner": eligible[0] if eligible else None,
              "runner_up": eligible[1] if len(eligible) > 1 else None,
              "excluded": excluded, "test": None}
    if result["winner"] and result["runner_up"]:
        w, u = result["winner"], result["runner_up"]
        result["test"] = two_prop_z(w["clicked_count"], w["sent_count"],
                                    u["clicked_count"], u["sent_count"])
    return result


def rate_cells(c: dict) -> list[str]:
    rt = rates(c)
    return [fmt(rt["open_rate"]), fmt(rt["ctr"]), fmt(rt["ctor"]), fmt(rt["unsub_rate"])]


def table(header: list[str], body: list[list]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(x) for x in row) + " |" for row in body]
    return out


def label(r: dict) -> str:
    return f"`{r['segment']}` / `{r['variant']}`"


def render_md(slug: str, rows, by_seg, by_var, total, win, ob, args) -> str:
    rate_hdr = ["Open Rate %", "CTR %", "CTOR %", "Unsub Rate %"]
    cnt = lambda c: [c["sent_count"], c["opened_count"], c["clicked_count"], c["unsubscribed_count"]]
    L = [f"## calc_metrics.py output: {slug}", "",
         f"Source: `{args.csv}` ({len(rows)} rows). Rates are exact fractions, rounded half-up to 2 dp.",
         "", "### By segment and variant", ""]
    L += table(["Segment", "Variant", "Sent", "Opened", "Clicked", "Unsubs"] + rate_hdr,
               [[r["segment"], r["variant"], *cnt(r), *rate_cells(r)]
                for r in sorted(rows, key=lambda r: (SEGMENTS.index(r["segment"]), r["variant"]))])
    L += ["", "### By segment (all variants)", ""]
    L += table(["Segment", "Sent", "Opened", "Clicked", "Unsubs"] + rate_hdr,
               [[k, *cnt(v), *rate_cells(v)] for k, v in
                sorted(by_seg.items(), key=lambda kv: SEGMENTS.index(kv[0]))])
    L += ["", "### By variant (all segments)", ""]
    L += table(["Variant", "Sent", "Opened", "Clicked", "Unsubs"] + rate_hdr,
               [[k, *cnt(v), *rate_cells(v)] for k, v in sorted(by_var.items())])
    if len(by_var) == 1:
        L += ["", f"Only one variant (`{next(iter(by_var))}`) in the data: no variant comparison possible."]
    L += ["", "### Campaign total", ""]
    L += table(["Sent", "Opened", "Clicked", "Unsubs"] + rate_hdr, [[*cnt(total), *rate_cells(total)]])
    L += ["", f"### Winner (highest CTR; min sent {args.min_sent}, unsub guardrail {args.max_unsub}%)", ""]
    w, u = win["winner"], win["runner_up"]
    if w:
        L.append(f"- **Winner:** {label(w)}: CTR {fmt(rates(w)['ctr'])}%, CTOR {fmt(rates(w)['ctor'])}%, "
                 f"Open {fmt(rates(w)['open_rate'])}%, Unsub {fmt(rates(w)['unsub_rate'])}%")
    else:
        L.append("- **Winner:** none (no row passed the guardrails)")
    if u:
        L.append(f"- **Runner-up:** {label(u)}: CTR {fmt(rates(u)['ctr'])}%")
        diff = rates(w)["ctr"] - rates(u)["ctr"]
        L.append(f"- **CTR gap:** {fmt(diff)} percentage points")
    if win["test"]:
        z, p = win["test"]
        sig = "significant at 95%" if p < 0.05 else "NOT significant at 95%"
        L.append(f"- **Two-proportion z-test (CTR, winner vs runner-up):** z = {z:.2f}, p = {p:.4f} ({sig})")
    for r, why in win["excluded"]:
        L.append(f"- Excluded {label(r)}: {why}")
    if ob is not None:
        L += ["", "### Outbox cross-check (list_outbox)", "",
              f"Practice sends for `{slug}`: {ob['practice_sends']}"
              f" (list_outbox count field: {ob['count_in_list']})", ""]
        L += table(["To", "Segment", "Variant (by subject)", "Sent at"],
                   [[s["to"], s["segment"], s["variant"], s["sent_at"]] for s in ob["sends"]])
        L += [""] + ([f"- ISSUE: {i}" for i in ob["issues"]] or
                     ["- OK: every metrics row has a matching practice send, all subjects match the draft, "
                      "all recipients are @example.com."])
    return "\n".join(L) + "\n"


def jsonable(c: dict) -> dict:
    out = {k: c[k] for k in COUNT_COLS}
    out.update({k: fmt(v) for k, v in rates(c).items()})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--csv", default="data/campaign-metrics.csv")
    ap.add_argument("--subscribers", default="data/subscribers.csv")
    ap.add_argument("--drafts", default="drafts")
    ap.add_argument("--outbox-json")
    ap.add_argument("--min-sent", type=int, default=100)
    ap.add_argument("--max-unsub", default="0.5")
    ap.add_argument("--format", choices=("md", "json"), default="md")
    args = ap.parse_args()

    if not SLUG_RE.fullmatch(args.slug):
        print(f"error: {args.slug!r} is not a valid slug", file=sys.stderr)
        return 2
    resolve = lambda p: (Path(p) if Path(p).is_absolute() else PROJECT_ROOT / p)
    csv_path = resolve(args.csv)
    if not csv_path.is_file():
        print(f"error: {csv_path} not found", file=sys.stderr)
        return 2

    rows, errors = load_rows(csv_path, args.slug)
    if errors:
        print("VALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    max_unsub = Fraction(args.max_unsub)
    by_seg, by_var, total = rollup(rows, "segment"), rollup(rows, "variant"), rollup(rows, None)["all"]
    win = pick_winner(rows, args.min_sent, max_unsub)
    ob = None
    if args.outbox_json:
        ob = outbox_check(args.outbox_json, args.slug, rows,
                          subscriber_segments(resolve(args.subscribers)),
                          draft_subjects(resolve(args.drafts), args.slug))

    if args.format == "json":
        out = {
            "campaign_slug": args.slug,
            "rows": [{"segment": r["segment"], "variant": r["variant"], **jsonable(r)} for r in rows],
            "by_segment": {k: jsonable(v) for k, v in by_seg.items()},
            "by_variant": {k: jsonable(v) for k, v in by_var.items()},
            "total": jsonable(total),
            "winner": win["winner"] and {"segment": win["winner"]["segment"],
                                         "variant": win["winner"]["variant"], **jsonable(win["winner"])},
            "runner_up": win["runner_up"] and {"segment": win["runner_up"]["segment"],
                                               "variant": win["runner_up"]["variant"]},
            "z_test": win["test"] and {"z": round(win["test"][0], 4), "p": round(win["test"][1], 6)},
            "excluded": [{"segment": r["segment"], "variant": r["variant"], "reason": why}
                         for r, why in win["excluded"]],
            "outbox": ob,
        }
        print(json.dumps(out, indent=2))
    else:
        print(render_md(args.slug, rows, by_seg, by_var, total, win, ob, args), end="")
    return 1 if ob and ob["issues"] else 0


if __name__ == "__main__":
    sys.exit(main())
