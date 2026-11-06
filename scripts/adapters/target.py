#!/usr/bin/env python3
"""Generic target renderers for agent-specific generated skill trees."""
from __future__ import annotations

import os
import re
import shutil
from typing import Any

from lib.skill_ir import SkillIR, yaml_quote

CODEX_ONLY_FILES = ("agents",)
IGNORED_DIRS = (".DS_Store", "__pycache__", "node_modules")


def _safe_name(name: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError(f"unsafe skill name: {name!r}")
    return name


def _copy_resources(record: SkillIR, skill_dir: str, *, include_agents: bool = False) -> None:
    source_dir = os.path.dirname(os.path.abspath(record.source))
    for entry in sorted(os.listdir(source_dir)):
        if entry == "SKILL.md" or (entry in CODEX_ONLY_FILES and not include_agents):
            continue
        source = os.path.join(source_dir, entry)
        target = os.path.join(skill_dir, entry)
        if os.path.isdir(source):
            if entry in IGNORED_DIRS:
                continue
            if os.path.exists(target):
                shutil.rmtree(target)
            shutil.copytree(source, target, ignore=shutil.ignore_patterns(*IGNORED_DIRS, "*.pyc"))
        elif entry in ("package.json", "package-lock.json"):
            shutil.copy2(source, target)


def _skill_markdown(record: SkillIR, *, include_model: bool = True) -> str:
    lines = ["---", f"name: {record.name}"]
    if include_model and record.model:
        lines.append(f"model: {yaml_quote(record.model)}")
    lines.append(f"description: {yaml_quote(record.description)}")
    if record.when_to_use:
        lines.append(f"whenToUse: {yaml_quote(record.when_to_use)}")
    if record.disable_model_invocation:
        lines.append("disable-model-invocation: true")
    if not record.user_invocable:
        lines.append("user-invocable: false")
    lines.extend(["---", "", record.body, ""])
    return "\n".join(lines)


def render_skill_directory(record: SkillIR, output_root: str, *, include_model: bool = True) -> str:
    safe_name = _safe_name(record.name)
    skill_dir = os.path.join(output_root, safe_name)
    os.makedirs(skill_dir, exist_ok=True)
    target = os.path.join(skill_dir, "SKILL.md")
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(_skill_markdown(record, include_model=include_model))
    _copy_resources(record, skill_dir)
    return target


def render_rule_file(record: SkillIR, output_root: str) -> str:
    safe_name = _safe_name(record.name)
    os.makedirs(output_root, exist_ok=True)
    target = os.path.join(output_root, f"{safe_name}.mdc")
    content = "---\n" f"description: {yaml_quote(record.description)}\n" "alwaysApply: false\n---\n\n" f"{record.body}\n"
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(content)
    return target


def render_prompt(record: SkillIR, output_root: str) -> str:
    safe_name = _safe_name(record.name)
    os.makedirs(output_root, exist_ok=True)
    target = os.path.join(output_root, f"{safe_name}.md")
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(f"---\nname: {safe_name}\ndescription: {yaml_quote(record.description)}\n---\n\n{record.body}\n")
    return target
