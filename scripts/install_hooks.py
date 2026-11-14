#!/usr/bin/env python3
"""Install the repo's Git pre-commit hook (stdlib only).

Run once after cloning:

    python scripts/install_hooks.py

Writes .git/hooks/pre-commit, which runs scripts/pre_commit_audit.py on every
`git commit`. Re-running is safe: it overwrites our own hook, and backs up any
other pre-commit hook it finds to pre-commit.backup first.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

MARKER = "# kettlebird-pre-commit-audit"

HOOK_TEMPLATE = """#!/bin/sh
{marker}
# Installed by scripts/install_hooks.py. Audits staged files before each commit.
ROOT="$(git rev-parse --show-toplevel)" || exit 1
AUDIT="$ROOT/scripts/pre_commit_audit.py"
if [ ! -f "$AUDIT" ]; then
  echo "pre-commit: $AUDIT not found; blocking commit." >&2
  exit 1
fi
for PY in "{python}" python3 python py; do
  if command -v "$PY" >/dev/null 2>&1 && "$PY" -c "import sys" >/dev/null 2>&1; then
    exec "$PY" "$AUDIT"
  fi
done
echo "pre-commit: no working Python found; blocking commit." >&2
exit 1
"""


def main() -> int:
    try:
        hooks_rel = subprocess.run(
            ["git", "rev-parse", "--git-path", "hooks"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("install_hooks: run this from inside the git repository.", file=sys.stderr)
        return 1

    hooks_dir = Path(hooks_rel).resolve()
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook = hooks_dir / "pre-commit"

    if hook.exists() and MARKER not in hook.read_text(encoding="utf-8", errors="replace"):
        backup = hook.with_name("pre-commit.backup")
        hook.replace(backup)
        print(f"install_hooks: existing hook moved to {backup}")

    python = Path(sys.executable).as_posix()
    hook.write_text(HOOK_TEMPLATE.format(marker=MARKER, python=python),
                    encoding="utf-8", newline="\n")
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"install_hooks: installed {hook}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
