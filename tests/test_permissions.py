"""Permission model tests: one per rule in docs/engagement/03-security-review.md."""
import copy
import json
import unittest
from datetime import timedelta
from pathlib import Path

from pilotkit.connectors import github, linear, notion, slack
from pilotkit.identity import Directory
from pilotkit.models import PUBLIC
from pilotkit.workspace import Workspace

WS = Path(__file__).resolve().parent.parent / "workspace" / "kestrel"


def native(source):
    return json.loads((WS / f"{source}.json").read_text())


class PermissionModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = Directory.load(WS / "directory.json")
        cls.ws = Workspace.load(WS)

    def acl(self, doc_id):
        return self.ws.get(doc_id).acl

    # GitHub
    def test_public_repo_is_readable_by_contractors(self):
        self.assertIn(PUBLIC, self.acl("github:docs-site/content/sdk/quickstart.md"))

    def test_internal_repo_excludes_outside_collaborators(self):
        acl = self.acl("github:ingest-gateway/README.md")
        self.assertIn("maya", acl)
        self.assertNotIn("alex", acl)

    def test_private_repo_limited_to_granted_teams(self):
        self.assertEqual(self.acl("github:security-tooling/detections/README.md"), {"rosa", "lee"})

    def test_private_repo_includes_direct_collaborator(self):
        self.assertEqual(self.acl("github:atlas-sdk/README.md"), {"dev", "jordan", "alex"})

    def test_unmapped_github_identity_is_dropped_and_reported(self):
        docs, report = github.normalize(native("github"), self.dir)
        self.assertIn("old-buildbot-2021", report.unmapped_identities)
        for d in docs:
            self.assertNotIn("old-buildbot-2021", d.acl)

    def test_unknown_visibility_fails_closed(self):
        n = copy.deepcopy(native("github"))
        n["repos"][0]["visibility"] = "something-new"
        docs, report = github.normalize(n, self.dir)
        self.assertFalse(any(d.id.startswith("github:ingest-gateway/") for d in docs))
        self.assertTrue(report.notes)

    # Slack
    def test_public_channel_excludes_guests(self):
        acl = self.acl("slack:C100/1729000001.0001")
        self.assertIn("dev", acl)
        self.assertNotIn("alex", acl)

    def test_private_channel_is_members_only(self):
        self.assertEqual(self.acl("slack:C300/1729200001.0001"), {"rosa", "lee", "tom"})

    def test_guest_sees_channel_they_were_added_to(self):
        self.assertIn("alex", self.acl("slack:C500/1729400001.0001"))

    def test_dm_is_participants_only(self):
        self.assertEqual(self.acl("slack:D600/1729500001.0001"), {"maya", "tom"})

    # Linear
    def test_private_linear_team(self):
        self.assertEqual(self.acl("linear:SEC-12"), {"rosa", "lee"})

    def test_contractor_not_in_linear_sees_no_issues(self):
        docs, _ = linear.normalize(native("linear"), self.dir)
        self.assertFalse(any("alex" in d.acl for d in docs))

    # Notion
    def test_restricted_page_shared_with_group(self):
        self.assertEqual(self.acl("notion:pg-comp-bands"), {"tom", "sam", "priya"})

    def test_restricted_page_shared_with_guest(self):
        self.assertIn("alex", self.acl("notion:pg-atlas-brief"))

    def test_workspace_page_excludes_guests(self):
        self.assertNotIn("alex", self.acl("notion:pg-onboarding"))

    # Freshness
    def test_stale_acls_are_excluded(self):
        ws = Workspace.load(WS, acl_ttl=timedelta(hours=1),
                            overrides={"slack": {**native("slack"), "synced_at": "2026-10-20T09:00:00Z"}})
        self.assertTrue(ws.stale_excluded)
        self.assertFalse(any(d.source == "slack" for d in ws.docs))


if __name__ == "__main__":
    unittest.main()
