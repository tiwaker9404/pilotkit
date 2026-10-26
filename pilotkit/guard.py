"""Quarantine retrieved chunks that look like prompt injection.

Not the real defense (that's the prefilter), just a second layer + a log entry for security.
"""
from __future__ import annotations

import re

INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above) (instructions|prompts|rules)",
    r"disregard (your|all|the) (instructions|rules|guidelines|permissions)",
    r"\b(ai|llm|assistant|chatbot)\b[^.]{0,40}\b(reading|processing) this",
    r"you are now (in )?(developer|admin|god) mode",
    r"reveal (the )?(system prompt|full contents|hidden)",
    r"this is an authori[sz]ed (test|request)",
]
_RX = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)


def looks_like_injection(text: str) -> bool:
    return bool(_RX.search(text))
