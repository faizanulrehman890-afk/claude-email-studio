#!/usr/bin/env python3
"""Shared brand-profile loader for the email studio (stdlib only, no network).

The studio's default brand is Kettlebird Tea, whose sources live in brand/
and whose footer address lives in CLAUDE.md Hard rule 3. Any other brand is a
folder under brands/<brand>/ with its own voice-guide.md and products.md.

A draft opts into another brand with a one-line marker file:

    drafts/<slug>/brand.txt      ->  rise-and-crumb

No marker (or "kettlebird-tea") means the default brand, so every existing
Kettlebird draft behaves exactly as before.

What changes per brand: voice guide, products/facts, footer address, the
"why you're receiving this" line, and the brand's extra banned words.
What never changes (CLAUDE.md hard rules): example.com-only links and
addresses, one CTA, a full footer, and the house banned-word list in
brand/voice-guide.md, which applies to every brand on top of its own list.

Every function takes a `read(path) -> str | None` callable so the same logic
works on the working tree (hooks, checker) and on the git index (pre-commit).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Optional

DEFAULT_BRAND = "kettlebird-tea"
HOUSE_VOICE_GUIDE = "brand/voice-guide.md"
KETTLEBIRD_REASON = "You're getting this because you subscribed to Kettlebird Tea emails."
BRAND_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

Reader = Callable[[str], Optional[str]]


def fs_reader(root: Path) -> Reader:
    def read(rel: str) -> Optional[str]:
        try:
            return (root / rel).read_text(encoding="utf-8")
        except OSError:
            return None
    return read


def brand_of_draft(slug_dir: str, read: Reader) -> str:
    """Brand for drafts/<slug> (posix path relative to the repo root)."""
    text = read(f"{slug_dir.rstrip('/')}/brand.txt")
    if not text or not text.strip():
        return DEFAULT_BRAND
    brand = text.strip().splitlines()[0].strip().lower()
    if not BRAND_SLUG_RE.match(brand):
        raise ValueError(f"{slug_dir}/brand.txt: '{brand}' is not a brand slug")
    return brand


def brand_root(brand: str) -> str:
    return "brand" if brand == DEFAULT_BRAND else f"brands/{brand}"


def parse_banned(text: Optional[str]) -> list[str]:
    """Bullet list under '## Banned words and phrases' in a voice guide."""
    if not text:
        return []
    m = re.search(r"^##\s+Banned words and phrases\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return []
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
    return list(dict.fromkeys(terms))


def _footer_field(products: str, field: str) -> Optional[str]:
    m = re.search(rf"^\|\s*{re.escape(field)}\s*\|\s*`?([^|`]+?)`?\s*\|", products, re.M)
    return m.group(1).strip() if m else None


def load_profile(brand: str, read: Reader) -> dict:
    """Return {brand, name, root, voice_guide, products, address, reason, banned, errors}."""
    root = brand_root(brand)
    profile = {
        "brand": brand, "root": root, "name": None, "address": None, "reason": None,
        "voice_guide": f"{root}/voice-guide.md", "products": f"{root}/products.md",
        "banned": [], "errors": [],
    }
    house = parse_banned(read(HOUSE_VOICE_GUIDE))
    guide = read(profile["voice_guide"])
    products = read(profile["products"])
    if guide is None:
        profile["errors"].append(f"missing {profile['voice_guide']}")
    if products is None:
        profile["errors"].append(f"missing {profile['products']}")

    # House list always applies; the brand's own list is added on top.
    profile["banned"] = list(dict.fromkeys(house + parse_banned(guide)))

    if brand == DEFAULT_BRAND:
        claude = read("CLAUDE.md") or ""
        m = re.search(r"^\s*(Kettlebird Tea, [^*\n]+?USA)", claude, re.M)
        profile.update(name="Kettlebird Tea", reason=KETTLEBIRD_REASON,
                       address=m.group(1).strip() if m else None)
    elif products is not None:
        profile.update(
            name=_footer_field(products, "Brand name"),
            address=_footer_field(products, "Mailing address"),
            reason=_footer_field(products, "Reason line"),
        )
        for key, field in (("name", "Brand name"), ("address", "Mailing address"),
                           ("reason", "Reason line")):
            if not profile[key]:
                profile["errors"].append(f"{profile['products']}: no '{field}' row in the Email footer table")
    return profile
