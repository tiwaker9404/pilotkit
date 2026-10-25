"""Prompt-injection guard.

Retrieved content is data, never instructions. Chunks that look like they are
trying to instruct the assistant are quarantined: kept out of the context,
never quoted, and logged as a security event for the customer's security team.

This is defense in depth. The real guarantee is that permission filtering
happens before retrieval, so even an injection that slipped through could
only ever see documents the asking user can already read.
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
