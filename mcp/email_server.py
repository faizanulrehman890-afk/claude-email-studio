#!/usr/bin/env python3
"""email-outbox: a local, practice-only "send" server for the Kettlebird email studio.

A Model Context Protocol (MCP) server speaking JSON-RPC 2.0 over stdio
(newline-delimited JSON). Zero external dependencies: standard library only.

Nothing here touches the network. "Sending" an email writes it to disk:

    outbox/<campaign_slug>/<timestamp>_<id>.json   full record (headers + both bodies)
    outbox/<campaign_slug>/<timestamp>_<id>.html   the HTML body, for opening in a browser

Tools
  send_test_email(to, subject, html_body, text_body, campaign_slug)
  list_outbox(campaign_slug=None)
  get_outbox_stats()

Safety rules (CLAUDE.md rule 4 and rule 7):
  * `to` must be a single address at exactly @example.com, or the send is rejected.
  * `campaign_slug` must be a plain slug (lowercase letters, digits, hyphens), so
    records can never be written outside outbox/.

Set EMAIL_OUTBOX_DIR to use a different outbox folder (handy for tests).
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SERVER_NAME = "email-outbox"
SERVER_VERSION = "1.0.0"
SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTBOX_DIR = Path(os.environ.get("EMAIL_OUTBOX_DIR") or PROJECT_ROOT / "outbox").resolve()

# One recipient, local part of ordinary characters, domain exactly example.com.
ALLOWED_TO = re.compile(r"^[A-Za-z0-9._%+-]+@example\.com$", re.IGNORECASE)
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SLUG_LEN = 80


class ToolError(Exception):
    """A problem with the tool's input; reported to the client as isError."""


# --------------------------------------------------------------------------- tools


def _require_str(args: dict[str, Any], name: str) -> str:
    value = args.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ToolError(f"`{name}` is required and must be a non-empty string.")
    return value


def _check_slug(slug: str) -> str:
    slug = slug.strip()
    if len(slug) > MAX_SLUG_LEN or not SLUG.fullmatch(slug):
        raise ToolError(
            f"campaign_slug {slug!r} is not a valid slug. Use lowercase letters, "
            "digits and single hyphens, e.g. 'steep-club-launch'."
        )
    return slug


def send_test_email(args: dict[str, Any]) -> dict[str, Any]:
    to = _require_str(args, "to").strip()
    subject = _require_str(args, "subject")
    html_body = _require_str(args, "html_body")
    text_body = _require_str(args, "text_body")
    slug = _check_slug(_require_str(args, "campaign_slug"))

    if not ALLOWED_TO.fullmatch(to):
        raise ToolError(
            f"Rejected: {to!r} is not an @example.com address. The practice outbox "
            "only accepts a single recipient at @example.com (CLAUDE.md rule 4)."
        )
    if "\n" in subject or "\r" in subject:
        raise ToolError("Rejected: subject must be a single line.")

    now = datetime.now(timezone.utc)
    short_id = uuid.uuid4().hex[:12]
    message_id = f"<practice-{short_id}@outbox.example.com>"
    stem = f"{now.strftime('%Y%m%dT%H%M%S%fZ')}_{short_id}"

    campaign_dir = OUTBOX_DIR / slug
    campaign_dir.mkdir(parents=True, exist_ok=True)
    json_path = campaign_dir / f"{stem}.json"
    html_path = campaign_dir / f"{stem}.html"

    record = {
        "message_id": message_id,
        "campaign_slug": slug,
        "to": to,
        "subject": subject,
        "sent_at": now.isoformat(timespec="seconds"),
        "practice_only": True,
        "html_file": html_path.name,
        "html_body": html_body,
        "text_body": text_body,
    }
    json_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    html_path.write_text(html_body, encoding="utf-8")

    return {
        "status": "saved to practice outbox (not sent)",
        "message_id": message_id,
        "to": to,
        "campaign_slug": slug,
        "record": _display_path(json_path),
    }


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def _iter_records(slug: str | None):
    if not OUTBOX_DIR.is_dir():
        return
    dirs = [OUTBOX_DIR / slug] if slug else sorted(p for p in OUTBOX_DIR.iterdir() if p.is_dir())
    for d in dirs:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                yield d.name, data


def list_outbox(args: dict[str, Any]) -> dict[str, Any]:
    slug = args.get("campaign_slug")
    if slug is not None:
        if not isinstance(slug, str):
            raise ToolError("`campaign_slug` must be a string when given.")
        slug = _check_slug(slug) if slug.strip() else None

    emails = [
        {
            "campaign_slug": campaign,
            "to": rec.get("to"),
            "subject": rec.get("subject"),
            "sent_at": rec.get("sent_at"),
            "message_id": rec.get("message_id"),
        }
        for campaign, rec in _iter_records(slug)
    ]
    emails.sort(key=lambda e: e.get("sent_at") or "")
    return {"count": len(emails), "emails": emails}


def get_outbox_stats(args: dict[str, Any]) -> dict[str, Any]:
    per_campaign: dict[str, int] = {}
    for campaign, _ in _iter_records(None):
        per_campaign[campaign] = per_campaign.get(campaign, 0) + 1
    return {
        "total": sum(per_campaign.values()),
        "per_campaign": dict(sorted(per_campaign.items())),
    }


TOOLS: dict[str, dict[str, Any]] = {
    "send_test_email": {
        "handler": send_test_email,
        "description": (
            "Practice-send an email to the LOCAL outbox only (nothing leaves this machine). "
            "`to` must be a single @example.com address; anything else is rejected. "
            "Saves a timestamped JSON + HTML record in outbox/<campaign_slug>/ and returns a fake message ID."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient; must end with @example.com."},
                "subject": {"type": "string", "description": "Subject line (single line)."},
                "html_body": {"type": "string", "description": "Full HTML body, e.g. drafts/<slug>/email.html."},
                "text_body": {"type": "string", "description": "Plain-text body, e.g. drafts/<slug>/email.txt."},
                "campaign_slug": {
                    "type": "string",
                    "description": "Campaign slug matching drafts/<slug>/, e.g. 'steep-club-launch'.",
                },
            },
            "required": ["to", "subject", "html_body", "text_body", "campaign_slug"],
            "additionalProperties": False,
        },
    },
    "list_outbox": {
        "handler": list_outbox,
        "description": "List practice emails in the local outbox with recipient, subject and timestamp. Optionally filter by campaign.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "campaign_slug": {"type": "string", "description": "Only list this campaign (optional)."},
            },
            "additionalProperties": False,
        },
    },
    "get_outbox_stats": {
        "handler": get_outbox_stats,
        "description": "Count practice emails in the local outbox, in total and per campaign.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
}


# ------------------------------------------------------------------ JSON-RPC / MCP


def _result(req_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle(msg: Any) -> dict[str, Any] | None:
    """Handle one JSON-RPC message. Returns a response, or None for notifications."""
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0" or not isinstance(msg.get("method"), str):
        req_id = msg.get("id") if isinstance(msg, dict) else None
        return _error(req_id, -32600, "Invalid Request")

    method = msg["method"]
    params = msg.get("params") or {}
    is_notification = "id" not in msg
    req_id = msg.get("id")

    if is_notification:
        return None  # notifications/initialized, notifications/cancelled, ...

    if method == "initialize":
        requested = params.get("protocolVersion")
        version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else SUPPORTED_PROTOCOL_VERSIONS[0]
        return _result(req_id, {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "instructions": (
                "Practice outbox for the Kettlebird email studio. Sends are saved to local files "
                "under outbox/ and never leave this machine. Only @example.com recipients are accepted."
            ),
        })

    if method == "ping":
        return _result(req_id, {})

    if method == "tools/list":
        return _result(req_id, {
            "tools": [
                {"name": name, "description": t["description"], "inputSchema": t["inputSchema"]}
                for name, t in TOOLS.items()
            ]
        })

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        tool = TOOLS.get(name)
        if tool is None:
            return _error(req_id, -32602, f"Unknown tool: {name!r}")
        if not isinstance(args, dict):
            return _error(req_id, -32602, "`arguments` must be an object.")
        try:
            payload = tool["handler"](args)
        except ToolError as exc:
            return _result(req_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
        except OSError as exc:
            return _result(req_id, {"content": [{"type": "text", "text": f"Outbox file error: {exc}"}], "isError": True})
        return _result(req_id, {
            "content": [{"type": "text", "text": json.dumps(payload, indent=2, ensure_ascii=False)}],
            "structuredContent": payload,
            "isError": False,
        })

    return _error(req_id, -32601, f"Method not found: {method}")


def main() -> None:
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer

    def write(obj: dict[str, Any]) -> None:
        stdout.write(json.dumps(obj, ensure_ascii=False).encode("utf-8") + b"\n")
        stdout.flush()

    for raw in stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            msg = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            write(_error(None, -32700, "Parse error"))
            continue

        if isinstance(msg, list):  # JSON-RPC batch (older protocol revisions)
            responses = [r for r in (handle(m) for m in msg) if r is not None]
            if responses:
                stdout.write(json.dumps(responses, ensure_ascii=False).encode("utf-8") + b"\n")
                stdout.flush()
            continue

        response = handle(msg)
        if response is not None:
            write(response)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
