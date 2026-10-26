"""Notion connector. Workspace pages -> members (no guests), restricted pages -> whoever they're shared with."""
from __future__ import annotations

from ..identity import Directory
from ..models import Document, SyncReport
from .base import IdentityMap, parse_ts


def normalize(native: dict, directory: Directory) -> tuple[list[Document], SyncReport]:
    report = SyncReport(source="notion")
    ids = IdentityMap(directory, {u["id"]: u.get("email") for u in native["users"]}, report)
    members = ids.resolve(u["id"] for u in native["users"] if u["type"] == "member")
    groups = {g["id"]: g["members"] for g in native.get("groups", [])}
    synced = parse_ts(native["synced_at"])

    docs = []
    for page in native["pages"]:
        if page["sharing"] == "workspace":
            acl = set(members)
        elif page["sharing"] == "restricted":
            acl = set()
            for principal in page["shared_with"]:
                acl |= ids.resolve(groups[principal]) if principal in groups else ids.resolve([principal])
        else:
            report.notes.append(f"{page['id']}: unknown sharing '{page['sharing']}', skipped")
            continue
        docs.append(Document(
            id=f"notion:{page['id']}",
            source="notion",
            container="Notion",
            title=page["title"],
            text=page["content"],
            url=f"https://www.notion.so/kestrel/{page['id']}",
            acl=frozenset(acl),
            synced_at=synced,
        ))
    report.documents = len(docs)
    return docs, report
