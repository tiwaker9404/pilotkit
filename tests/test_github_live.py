"""The live GitHub connector, tested against recorded API-shaped responses."""
import base64
import unittest
from pathlib import Path
from unittest import mock

from pilotkit.connectors import github
from pilotkit.models import PUBLIC
from pilotkit.workspace import Workspace

WS = Path(__file__).resolve().parent.parent / "workspace" / "kestrel"

PAGES = {
    "/orgs/acme/members": [{"login": "mokafor"}, {"login": "devr-k"}],
    "/orgs/acme/teams": [{"slug": "platform"}],
    "/orgs/acme/teams/platform/members": [{"login": "mokafor"}],
    "/orgs/acme/outside_collaborators": [{"login": "alexc-nw"}],
    "/orgs/acme/repos?type=all": [
        {"name": "infra", "visibility": "private", "default_branch": "main"},
        {"name": "handbook", "visibility": "internal", "default_branch": "main"},
    ],
    "/repos/acme/infra/teams": [{"slug": "platform", "permission": "admin"}],
    "/repos/acme/infra/collaborators?affiliation=direct": [],
    "/repos/acme/handbook/teams": [],
    "/repos/acme/handbook/collaborators?affiliation=direct": [],
}
GETS = {
    "/repos/acme/infra/git/trees/main?recursive=1": {"tree": [
        {"type": "blob", "path": "README.md", "sha": "a1", "size": 50},
        {"type": "blob", "path": "src/main.go", "sha": "a2", "size": 50},
    ]},
    "/repos/acme/handbook/git/trees/main?recursive=1": {"tree": [
        {"type": "blob", "path": "docs/oncall.md", "sha": "b1", "size": 50},
    ]},
    "/repos/acme/infra/git/blobs/a1": {"content": base64.b64encode(b"Infra readme").decode()},
    "/repos/acme/handbook/git/blobs/b1": {"content": base64.b64encode(b"On-call guide").decode()},
}


class LiveGitHub(unittest.TestCase):
    def test_fetch_and_normalize(self):
        emails = {"mokafor": "maya@kestrel.dev", "devr-k": "dev@kestrel.dev", "alexc-nw": "alex@northwind.studio"}
        with mock.patch.object(github.GitHubClient, "paginate", side_effect=lambda p: PAGES[p]), \
             mock.patch.object(github.GitHubClient, "get", side_effect=lambda p: GETS[p]):
            native = github.fetch_native("acme", "t0ken", emails)
        ws = Workspace.load(WS, overrides={"github": native})
        infra = ws.get("github:infra/README.md")
        handbook = ws.get("github:handbook/docs/oncall.md")
        self.assertEqual(infra.acl, {"maya"})              # private: team members only
        self.assertEqual(handbook.acl, {"maya", "dev"})    # internal: org members, no outside collaborator
        self.assertNotIn(PUBLIC, handbook.acl)
        self.assertIsNone(ws.get("github:infra/src/main.go"))  # only docs are indexed


if __name__ == "__main__":
    unittest.main()
