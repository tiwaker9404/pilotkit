"""Loads a customer workspace: directory + every connected source.

Ingest pipeline: native payload -> normalize (ACLs as user ids) -> redact
secrets/PII -> freshness check on permissions -> ready for retrieval.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from pathlib import Path

from .connectors import NORMALIZERS
from .identity import Directory
from .models import Document, SyncReport
from .redact import redact

SOURCES = ("github", "slack", "linear", "notion")


@dataclass
class Workspace:
    directory: Directory
    docs: list[Document]
    reports: list[SyncReport]
    redactions: dict[str, list[str]] = field(default_factory=dict)
    stale_excluded: list[str] = field(default_factory=list)

    @classmethod
    def load(
        cls,
        path: Path | str,
        acl_ttl: timedelta = timedelta(hours=24),
        as_of: datetime | None = None,
        overrides: dict[str, dict] | None = None,
    ) -> "Workspace":
        """Load fixtures from `path`. `overrides` swaps in a native payload per
        source, which is how live connectors (e.g. GitHub) plug in."""
        path = Path(path)
        directory = Directory.load(path / "directory.json")
        overrides = overrides or {}
        docs, reports, redactions = [], [], {}
        for source in SOURCES:
            native = overrides.get(source)
            if native is None:
                f = path / f"{source}.json"
                if not f.exists():
                    continue
                native = json.loads(f.read_text())
            source_docs, report = NORMALIZERS[source](native, directory)
            for d in source_docs:
                clean_title, _ = redact(d.title)
                clean_text, hits = redact(d.text)
                if hits:
                    redactions[d.id] = hits
                docs.append(replace(d, title=clean_title, text=clean_text))
            reports.append(report)

        # Permission freshness: if a source's ACLs haven't been re-synced within
        # the TTL, we can't trust them (someone may have been removed from a
        # channel). Fail closed: exclude those documents.
        as_of = as_of or max((d.synced_at for d in docs), default=None)
        fresh, stale = [], []
        for d in docs:
            if as_of is not None and as_of - d.synced_at > acl_ttl:
                stale.append(d.id)
            else:
                fresh.append(d)
        return cls(directory, fresh, reports, redactions, stale)

    def readable(self, user_id: str) -> list[Document]:
        return [d for d in self.docs if d.readable_by(user_id)]

    def get(self, doc_id: str) -> Document | None:
        return next((d for d in self.docs if d.id == doc_id), None)
