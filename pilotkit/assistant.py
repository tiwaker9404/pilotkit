"""permission filter -> retrieve -> guard -> answer -> redact -> audit

modes:
  prefilter   only search docs the user can read (default)
  postfilter  search everything, drop unreadable hits after
  none        no filtering, only exists so the red team has a baseline
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .answer import REFUSAL, default_answerer
from .guard import looks_like_injection
from .index import BM25
from .models import Answer, Citation
from .redact import redact
from .workspace import Workspace

MODES = ("prefilter", "postfilter", "none")


class Assistant:
    def __init__(self, workspace: Workspace, mode: str = "prefilter", answerer=None,
                 k: int = 5, audit_path: Path | str | None = None):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        self.ws = workspace
        self.mode = mode
        self.k = k
        self.answerer = answerer or default_answerer(workspace.directory.company["name"])
        self.audit_path = Path(audit_path) if audit_path else None
        self._global = BM25(workspace.docs)
        self._per_user: dict[str, BM25] = {}

    def _index_for(self, user_id: str) -> BM25:
        if user_id not in self._per_user:
            self._per_user[user_id] = BM25(self.ws.readable(user_id))
        return self._per_user[user_id]

    def retrieve(self, user_id: str, question: str):
        """Return (hits, idf) for the user under the configured ACL mode."""
        if self.mode == "prefilter":
            index = self._index_for(user_id)
            return index.search(question, self.k), index.idf
        hits = self._global.search(question, self.k)
        if self.mode == "postfilter":
            hits = [h for h in hits if h.doc.readable_by(user_id)]
        return hits, self._global.idf

    def ask(self, user_id: str, question: str) -> Answer:
        self.ws.directory.get(user_id)  # unknown users are rejected, not defaulted
        t0 = time.perf_counter()
        hits, idf = self.retrieve(user_id, question)
        quarantined = [h.doc.id for h in hits if looks_like_injection(h.doc.text)]
        clean_hits = [h for h in hits if h.doc.id not in quarantined]

        draft = self.answerer.answer(question, clean_hits, idf)
        text, _ = redact(draft.text)
        citations = []
        if not draft.refused:
            for n, idx in enumerate(draft.cited, start=1):
                d = clean_hits[idx].doc
                citations.append(Citation(n=n, doc_id=d.id, source=d.source, title=d.title,
                                          url=d.url, snippet=d.text[:160]))
        ans = Answer(
            question=question, user_id=user_id, text=text if not draft.refused else REFUSAL,
            citations=citations, refused=draft.refused, mode=self.mode,
            retrieved_ids=[h.doc.id for h in clean_hits], quarantined_ids=quarantined,
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
        )
        self._audit(ans)
        return ans

    def _audit(self, ans: Answer) -> None:
        """Append-only audit record. Stores doc ids, not content, so the log
        itself never becomes a second copy of restricted data."""
        if not self.audit_path:
            return
        rec = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "user": ans.user_id,
            "mode": ans.mode,
            "question": redact(ans.question)[0],
            "refused": ans.refused,
            "cited": [c.doc_id for c in ans.citations],
            "retrieved": ans.retrieved_ids,
            "security_events": [{"type": "prompt_injection_quarantined", "doc": d} for d in ans.quarantined_ids],
            "latency_ms": ans.latency_ms,
        }
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a") as f:
            f.write(json.dumps(rec) + "\n")
