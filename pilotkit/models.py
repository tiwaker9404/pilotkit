"""Core data types."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

PUBLIC = "public"  # principal granted to everyone, including contractors


@dataclass(frozen=True)
class Document:
    # acl = user ids (or PUBLIC). connectors expand teams/channels/groups at sync time

    id: str
    source: str            # github | slack | linear | notion
    container: str         # repo, channel, team or page the item lives in
    title: str
    text: str
    url: str
    acl: frozenset[str]
    synced_at: datetime
    author: str | None = None

    def readable_by(self, user_id: str) -> bool:
        return PUBLIC in self.acl or user_id in self.acl


@dataclass
class SyncReport:
    source: str
    documents: int = 0
    unmapped_identities: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def warn_unmapped(self, native_id: str) -> None:
        if native_id not in self.unmapped_identities:
            self.unmapped_identities.append(native_id)


@dataclass
class Citation:
    n: int
    doc_id: str
    source: str
    title: str
    url: str
    snippet: str


@dataclass
class Answer:
    question: str
    user_id: str
    text: str
    citations: list[Citation]
    refused: bool
    mode: str
    retrieved_ids: list[str]
    quarantined_ids: list[str]
    latency_ms: float
