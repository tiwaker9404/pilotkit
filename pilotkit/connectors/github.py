"""GitHub connector.

public repo   -> everyone
internal repo -> org members (not outside collaborators) + collaborators
private repo  -> granted teams + direct collaborators
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.request

from ..identity import Directory
from ..models import PUBLIC, Document, SyncReport
from .base import IdentityMap, parse_ts


def normalize(native: dict, directory: Directory) -> tuple[list[Document], SyncReport]:
    report = SyncReport(source="github")
    emails = {m["login"]: m.get("saml_email") for m in native["members"]}
    emails.update({c["login"]: c.get("email") for c in native.get("outside_collaborators", [])})
    ids = IdentityMap(directory, emails, report)
    org_members = ids.resolve(m["login"] for m in native["members"] if m.get("saml_email"))
    teams = {t["slug"]: t["members"] for t in native["teams"]}
    synced = parse_ts(native["synced_at"])
    org = native["org"]

    docs = []
    for repo in native["repos"]:
        collaborators = ids.resolve(c["login"] for c in repo.get("collaborators", []))
        vis = repo["visibility"]
        if vis == "public":
            acl = {PUBLIC}
        elif vis == "internal":
            acl = set(org_members) | collaborators
        elif vis == "private":
            acl = set(collaborators)
            for grant in repo.get("teams", []):
                acl |= ids.resolve(teams.get(grant["slug"], []))
        else:  # unknown visibility: fail closed
            report.notes.append(f"{repo['name']}: unknown visibility '{vis}', skipped")
            continue
        for f in repo["files"]:
            docs.append(Document(
                id=f"github:{repo['name']}/{f['path']}",
                source="github",
                container=f"{org}/{repo['name']}",
                title=f.get("title") or f"{repo['name']}/{f['path']}",
                text=f["content"],
                url=f"https://github.com/{org}/{repo['name']}/blob/main/{f['path']}",
                acl=frozenset(acl),
                synced_at=synced,
            ))
    report.documents = len(docs)
    return docs, report


# --------------------------------------------------------------------------
# Live mode: fetch the same native shape from the GitHub REST API.
# --------------------------------------------------------------------------

API = "https://api.github.com"
DOC_PATH = re.compile(r"^(README\.md|docs/.+\.md)$", re.IGNORECASE)


class GitHubClient:
    def __init__(self, token: str):
        self.token = token

    def _req(self, url: str):
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "pilotkit",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode())
            return body, resp.headers.get("Link", "")

    def get(self, path: str):
        body, _ = self._req(f"{API}{path}")
        return body

    def paginate(self, path: str) -> list:
        sep = "&" if "?" in path else "?"
        url, out = f"{API}{path}{sep}per_page=100", []
        while url:
            body, link = self._req(url)
            out.extend(body)
            m = re.search(r'<([^>]+)>;\s*rel="next"', link)
            url = m.group(1) if m else None
        return out


def fetch_native(org: str, token: str, identity_emails: dict[str, str], max_repos: int = 50) -> dict:
    # GitHub doesn't return corporate emails on the REST user object, so the
    # login -> email map comes in as a CSV instead of guessing.
    from datetime import datetime, timezone

    gh = GitHubClient(token)
    members = [{"login": m["login"], "saml_email": identity_emails.get(m["login"])}
               for m in gh.paginate(f"/orgs/{org}/members")]
    teams = []
    for t in gh.paginate(f"/orgs/{org}/teams"):
        tm = gh.paginate(f"/orgs/{org}/teams/{t['slug']}/members")
        teams.append({"slug": t["slug"], "members": [m["login"] for m in tm]})
    outside = [{"login": c["login"], "email": identity_emails.get(c["login"])}
               for c in gh.paginate(f"/orgs/{org}/outside_collaborators")]

    repos = []
    for r in gh.paginate(f"/orgs/{org}/repos?type=all")[:max_repos]:
        name = r["name"]
        grants = [{"slug": t["slug"], "permission": t.get("permission", "pull")}
                  for t in gh.paginate(f"/repos/{org}/{name}/teams")]
        collabs = [{"login": c["login"]}
                   for c in gh.paginate(f"/repos/{org}/{name}/collaborators?affiliation=direct")]
        files = []
        tree = gh.get(f"/repos/{org}/{name}/git/trees/{r['default_branch']}?recursive=1")
        for node in tree.get("tree", []):
            if node["type"] == "blob" and DOC_PATH.match(node["path"]) and node.get("size", 0) < 200_000:
                blob = gh.get(f"/repos/{org}/{name}/git/blobs/{node['sha']}")
                text = base64.b64decode(blob["content"]).decode("utf-8", "replace")
                files.append({"path": node["path"], "title": f"{name}/{node['path']}", "content": text})
        repos.append({"name": name, "visibility": r.get("visibility", "private"),
                      "teams": grants, "collaborators": collabs, "files": files})

    return {
        "org": org,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "members": members,
        "outside_collaborators": outside,
        "teams": teams,
        "repos": repos,
    }


def token_from_env() -> str | None:
    return os.environ.get("GITHUB_TOKEN")
