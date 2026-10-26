"""Directory + identity resolution. Everything joins on email; ids we can't map get dropped."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class User:
    id: str
    name: str
    email: str
    title: str
    type: str  # employee | contractor
    groups: tuple[str, ...]
    persona: str = ""


class Directory:
    def __init__(self, company: dict, users: list[User]):
        self.company = company
        self.users = {u.id: u for u in users}
        self._by_email = {u.email.lower(): u for u in users}

    @classmethod
    def load(cls, path: Path) -> "Directory":
        raw = json.loads(Path(path).read_text())
        users = [
            User(
                id=u["id"], name=u["name"], email=u["email"], title=u["title"],
                type=u["type"], groups=tuple(u["groups"]), persona=u.get("persona", ""),
            )
            for u in raw["users"]
        ]
        return cls(raw["company"], users)

    def by_email(self, email: str | None) -> User | None:
        if not email:
            return None
        return self._by_email.get(email.lower())

    def get(self, user_id: str) -> User:
        if user_id not in self.users:
            known = ", ".join(sorted(self.users))
            raise KeyError(f"Unknown user '{user_id}'. Known users: {known}")
        return self.users[user_id]

    def personas(self) -> list[User]:
        return [u for u in self.users.values() if u.persona]
