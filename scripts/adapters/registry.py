"""Configurable agent adapter registry."""
from __future__ import annotations
import importlib

ADAPTERS = {
    "dsh": "adapters.dsh",
    "codex": "adapters.codex",
    "cline": "adapters.cline",
    "cursor": "adapters.cursor",
    "gemini": "adapters.gemini",
    "pi": "adapters.pi",
}

def get_adapter(name: str):
    try:
        return importlib.import_module(ADAPTERS[name])
    except KeyError as exc:
        raise ValueError(f"unknown target {name!r}; choose one of: {', '.join(sorted(ADAPTERS))}") from exc
