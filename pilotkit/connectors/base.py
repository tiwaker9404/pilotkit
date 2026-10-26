"""Helpers shared by the connectors."""
from __future__ import annotations

from datetime import datetime

from ..identity import Directory
from ..models import SyncReport


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class IdentityMap:
    """Maps a source's native user ids to directory user ids via email."""

    def __init__(self, directory: Directory, native_to_email: dict[str, str | None], report: SyncReport):
        self.report = report
        self._map: dict[str, str] = {}
        for native_id, email in native_to_email.items():
            user = directory.by_email(email)
            if user is None:
                report.warn_unmapped(native_id)
            else:
                self._map[native_id] = user.id

    def resolve(self, native_ids) -> set[str]:
        out = set()
        for nid in native_ids:
            uid = self._map.get(nid)
            if uid is None:
                self.report.warn_unmapped(nid)
            else:
                out.add(uid)
        return out

    def one(self, native_id: str | None) -> str | None:
        return self._map.get(native_id) if native_id else None

    def all_users(self) -> set[str]:
        return set(self._map.values())
