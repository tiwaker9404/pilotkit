"""Linear connector. Public team -> all workspace members, private team -> team members."""
from __future__ import annotations

from ..identity import Directory
from ..models import Document, SyncReport
from .base import IdentityMap, parse_ts


def normalize(native: dict, directory: Directory) -> tuple[list[Document], SyncReport]:
    report = SyncReport(source="linear")
    ids = IdentityMap(directory, {u["id"]: u.get("email") for u in native["users"]}, report)
    everyone = ids.all_users()
    teams = {t["key"]: t for t in native["teams"]}
    synced = parse_ts(native["synced_at"])

    docs = []
    for issue in native["issues"]:
        team = teams.get(issue["team"])
        if team is None:
            report.notes.append(f"{issue['identifier']}: unknown team, skipped")
            continue
        acl = ids.resolve(team["members"]) if team["private"] else everyone
        docs.append(Document(
            id=f"linear:{issue['identifier']}",
            source="linear",
            container=f"{team['name']} team",
            title=f"{issue['identifier']}: {issue['title']}",
            text=f"{issue['identifier']} ({issue['title']}) is {issue['state']}. {issue['description']}",
            url=f"https://linear.app/kestrel/issue/{issue['identifier']}",
            acl=frozenset(acl),
            synced_at=synced,
            author=ids.one(issue.get("assignee")),
        ))
    report.documents = len(docs)
    return docs, report
