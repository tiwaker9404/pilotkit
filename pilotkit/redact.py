"""Redact secrets and PII. Runs at ingest and again on answers."""
from __future__ import annotations

import re

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("AWS_KEY", re.compile(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("GITHUB_TOKEN", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("API_KEY", re.compile(r"\b(sk|pk|rk)_(live|test)_[A-Za-z0-9]{10,}\b")),
    ("SLACK_TOKEN", re.compile(r"\bxox[abpors]-[A-Za-z0-9-]{10,}\b")),
    ("PRIVATE_KEY", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("CARD", re.compile(r"\b(?:\d[ -]?){13,16}\b")),
    ("PHONE", re.compile(r"(?<!\d)(?:\+1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)")),
]

EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")


def redact(text: str, internal_domains: tuple[str, ...] = ("kestrel.dev",)) -> tuple[str, list[str]]:
    # keep internal emails, redact external ones (customer contacts aren't covered by the DPA)
    hits: list[str] = []
    for kind, pattern in PATTERNS:
        text, n = pattern.subn(f"[REDACTED:{kind}]", text)
        hits += [kind] * n

    def _email(m: re.Match) -> str:
        if m.group(1).lower() in internal_domains:
            return m.group(0)
        hits.append("EXTERNAL_EMAIL")
        return "[REDACTED:EXTERNAL_EMAIL]"

    text = EMAIL.sub(_email, text)
    return text, hits
