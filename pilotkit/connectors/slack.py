"""Slack connector.

Permission model:
  public channel  -> every full workspace member (guests are excluded unless
                     they are explicitly in the channel)
  private channel -> channel members only
  DM / group DM   -> participants only
Each message becomes one Document so citations can point at the exact message.
"""
from __future__ import annotations

from ..identity import Directory
from ..models import Document, SyncReport
from .base import IdentityMap, parse_ts


def normalize(native: dict, directory: Directory) -> tuple[list[Document], SyncReport]:
    report = SyncReport(source="slack")
    ids = IdentityMap(directory, {u["id"]: u["profile"].get("email") for u in native["users"]}, report)
    full_members = ids.resolve(u["id"] for u in native["users"] if not u.get("is_restricted"))
    synced = parse_ts(native["synced_at"])
    ws = native["workspace"]

    docs = []
    for ch in native["channels"]:
        explicit = ids.resolve(ch.get("members", []))
        acl = explicit if ch["is_private"] else (full_members | explicit)
        label = ch["name"] if ch.get("is_im") else f"#{ch['name']}"
        for msg in ch["messages"]:
            ts = msg["ts"].replace(".", "")
            docs.append(Document(
                id=f"slack:{ch['id']}/{msg['ts']}",
                source="slack",
                container=label,
                title=f"{label} message",
                text=msg["text"],
                url=f"https://{ws}.slack.com/archives/{ch['id']}/p{ts}",
                acl=frozenset(acl),
                synced_at=synced,
                author=ids.one(msg.get("user")),
            ))
    report.documents = len(docs)
    return docs, report
