"""Dependency-free BM25 retrieval.

Small on purpose: for a pilot over a few thousand documents BM25 is fast,
explainable and good enough, and it keeps the permission story easy to audit.
The `BM25` class is the seam where a vector store would plug in for a larger rollout.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from .models import Document

STOPWORDS = set("""
a an and are as at be but by can do does for from get got has have how i if in into is it its
me my of on or our should so that the their them then there these they this to up us was we
what when where which who why will with would you your about any some need know tell please
happen happened happening much many does did done going go use used mean say said like find show give
hey hi thanks thank anyone someone currently right now just still also there's what's came come up
""".split())

_TOKEN = re.compile(r"[a-z0-9]+")


MONTHS = {m: m[:3] for m in ("january", "february", "march", "april", "june", "july", "august",
                              "september", "october", "november", "december")}
MONTHS.update({"sept": "sep"})

# Small synonym table: the words engineers ask with vs the words docs use.
SYNONYMS = {"env": "environment", "finish": "done", "finished": "done", "complete": "done",
            "completed": "done", "repo": "repository", "db": "database", "k8s": "kubernetes",
            "prod": "production", "pr": "pull", "salary": "compensation", "comp": "compensation"}


def stem(t: str) -> str:
    t = SYNONYMS.get(t, t)
    if t in MONTHS:
        return MONTHS[t]
    if t.endswith("ally") and len(t) > 6:
        t = t[:-2]
    if len(t) > 4 and t.endswith("s") and not t.endswith("ss"):
        t = t[:-1]  # plural first, so "findings" -> "finding" -> "find"
    for suf, repl in (("ations", "at"), ("ation", "at"), ("ingly", ""), ("ing", ""), ("edly", ""),
                      ("ed", ""), ("ies", "y"), ("es", ""), ("s", "")):
        if len(t) > len(suf) + 2 and t.endswith(suf):
            t = t[: -len(suf)] + repl
            break
    if len(t) > 4 and t.endswith("e"):
        t = t[:-1]
    return t


def tokenize(text: str) -> list[str]:
    return [stem(t) for t in _TOKEN.findall(text.lower()) if t not in STOPWORDS]


@dataclass
class Hit:
    doc: Document
    score: float


class BM25:
    def __init__(self, docs: list[Document], k1: float = 1.4, b: float = 0.75):
        self.docs = docs
        self.k1, self.b = k1, b
        self.tfs = [Counter(tokenize(d.title + " " + d.text)) for d in docs]
        self.lens = [sum(tf.values()) for tf in self.tfs]
        self.avg = (sum(self.lens) / len(self.lens)) if docs else 0.0
        df: Counter = Counter()
        for tf in self.tfs:
            df.update(tf.keys())
        n = len(docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def search(self, query: str, k: int = 5) -> list[Hit]:
        q = tokenize(query)
        scored = []
        for i, tf in enumerate(self.tfs):
            s = 0.0
            for t in q:
                f = tf.get(t)
                if not f:
                    continue
                denom = f + self.k1 * (1 - self.b + self.b * self.lens[i] / (self.avg or 1))
                s += self.idf[t] * f * (self.k1 + 1) / denom
            if s > 0:
                scored.append(Hit(self.docs[i], s))
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:k]
