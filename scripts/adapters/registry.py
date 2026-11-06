"""Named agent adapters for the canonical Parse → IR → Render pipeline."""
from __future__ import annotations

from typing import Callable

from adapters import codex, dsh

ADAPTERS = {
    "dsh": dsh,
    "codex": codex,
}


def get_adapter(name: str):
    try:
        return ADAPTERS[name]
    except KeyError as exc:
        choices = ", ".join(sorted(ADAPTERS))
        raise ValueError(f"unknown target {name!r}; choose one of: {choices}") from exc
