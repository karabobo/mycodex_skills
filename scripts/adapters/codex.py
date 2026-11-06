#!/usr/bin/env python3
"""Codex target adapter.

Codex is the canonical source format, so this adapter deliberately preserves
its frontmatter/body and only materializes a target tree for tooling that wants
an explicit per-agent output. Keeping it as a target makes adding another agent
an isolated adapter rather than another one-off rewrite of every skill.
"""
from __future__ import annotations

import os
import shutil

from lib.skill_ir import SkillIR, yaml_quote


def render_skill(record: SkillIR, output_root: str, max_length: int = 0) -> str:
    skill_dir = os.path.join(output_root, record.name)
    os.makedirs(skill_dir, exist_ok=True)
    target = os.path.join(skill_dir, "SKILL.md")
    lines = ["---", f"name: {record.name}", f"description: {yaml_quote(record.description)}"]
    if record.when_to_use:
        lines.append(f"whenToUse: {yaml_quote(record.when_to_use)}")
    if record.disable_model_invocation:
        lines.append("disable-model-invocation: true")
    if not record.user_invocable:
        lines.append("user-invocable: false")
    lines.extend(["---", "", record.body, ""])
    with open(target, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    source_dir = os.path.dirname(os.path.abspath(record.source))
    for entry in os.listdir(source_dir):
        if entry == "SKILL.md":
            continue
        source = os.path.join(source_dir, entry)
        if not os.path.isdir(source):
            continue
        destination = os.path.join(skill_dir, entry)
        if os.path.exists(destination):
            shutil.rmtree(destination)
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return target


def render_all(records: list[SkillIR], output_root: str, max_length: int = 0) -> list[str]:
    if os.path.isdir(output_root):
        shutil.rmtree(output_root)
    os.makedirs(output_root, exist_ok=True)
    return [render_skill(record, output_root, max_length) for record in records]
