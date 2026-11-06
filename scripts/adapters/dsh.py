#!/usr/bin/env python3
"""DSH renderer — render SkillIR records into a DeepSeek Harness skill tree.

DSH differs from Codex in ways that matter for a skill to load correctly.
This renderer is the only place those differences are expressed.

The contract, taken from the DSH source (not guessed):

1. Layout. A skill is ``<root>/<name>/SKILL.md`` — a directory bundle, or a
   flat ``<root>/<name>.md``. Nested ``**/SKILL.md`` is deliberately NOT
   discovered, so sibling markdown has to be folded into the body.

2. Frontmatter. ``name`` and ``description`` are required. ``whenToUse``,
   ``metadata``, ``disable-model-invocation`` and ``user-invocable`` are
   optional. The legacy keys ``disableModelInvocation``, ``modelInvocable``
   and ``userInvocable`` are rejected outright, so a Codex skill carrying
   them fails to load at all — they are dropped here.

3. Description cap. The catalog truncates descriptions at 500 normalized
   characters, silently cutting the tail off. A truncated scope clause
   ("Do not use this skill for Chinese-language or...") misroutes the model
   to the wrong sibling skill, so the renderer rebalances the description
   instead of letting DSH chop it.

4. Invocation policy. ``disable-model-invocation`` keeps the model from
   auto-triggering a skill; ``user-invocable: false`` keeps it out of the
   user's slash-command list. Both default to permitted.

5. Codex-only artifacts (``agents/openai.yaml``) are dropped. DSH never
   reads them.
"""

from __future__ import annotations

import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.skill_ir import (  # noqa: E402
    CATALOG_DESCRIPTION_MAX_LENGTH,
    SkillIR,
    normalize_description,
    yaml_quote,
)

# The Codex frontmatter keys DSH rejects. Carrying them over makes the
# skill fail to load, so they are stripped rather than translated.
CODEX_ONLY_FRONTMATTER_KEYS = (
    "disableModelInvocation",
    "modelInvocable",
    "userInvocable",
)

# Files that carry meaning for Codex but are inert in DSH.
CODEX_ONLY_FILES = ("agents",)


def _split_description(description: str) -> tuple[str, str]:
    """Split a description into (primary, negative-scope).

    The negative scope is the clause that says when NOT to use the skill —
    "Do not use this skill for X". DSH's catalog only has room for one
    string, so the renderer has to decide which half survives truncation.
    The negative clause always wins: losing it sends the model to the
    wrong sibling skill, while losing detail from the positive clause
    merely makes the skill slightly less specific.
    """
    normalized = normalize_description(description)
    marker = re.search(r"\b(?:do not use|don't use|not for|not use)\b", normalized, re.I)
    if not marker:
        return normalized, ""
    return normalized[: marker.start()].rstrip(" ,;"), normalized[marker.start():].strip()


def _rebalance_description(description: str, max_length: int) -> str:
    """Fit a description into DSH's catalog without losing its scope clause.

    Strategy, in order:
      1. If it already fits, keep it verbatim.
      2. Otherwise drop the least load-bearing trailing sentences of the
         positive clause until the whole thing fits.
      3. If even the bare primary clause does not fit, truncate it the way
         DSH would — but keep the negative clause intact and prefixed, so
         the model still sees the boundary.
    """
    normalized = normalize_description(description)
    if len(normalized) <= max_length:
        return normalized

    primary, negative = _split_description(normalized)
    if not negative:
        return normalize_description(primary)[: max_length - 3] + "..."

    budget = max_length - len(negative) - 1
    if budget > 0 and len(primary) > budget:
        # Drop trailing sentences from the primary clause first.
        sentences = re.split(r"(?<=[.!?])\s+", primary)
        kept = sentences[0] if sentences else primary
        for sentence in sentences[1:]:
            candidate = f"{kept} {sentence}".strip()
            if len(candidate) + 1 + len(negative) > max_length:
                break
            kept = candidate
        primary = kept
        if len(primary) > budget:
            primary = primary[:budget].rstrip(" ,;.")

    return f"{primary} {negative}".strip()


def render_frontmatter(record: SkillIR, max_length: int = CATALOG_DESCRIPTION_MAX_LENGTH) -> str:
    """Render the DSH frontmatter block for one skill."""
    description = _rebalance_description(record.description, max_length)
    lines = [
        "---",
        f"name: {record.name}",
        f"description: {yaml_quote(description)}",
    ]
    if record.when_to_use:
        lines.append(f"whenToUse: {yaml_quote(record.when_to_use)}")
    if record.disable_model_invocation:
        lines.append("disable-model-invocation: true")
    if not record.user_invocable:
        lines.append("user-invocable: false")
    lines.append("---")
    return "\n".join(lines)


def render_skill(record: SkillIR, output_root: str, max_length: int = CATALOG_DESCRIPTION_MAX_LENGTH) -> str:
    """Render one skill into ``output_root`` and return the written path."""
    skill_dir = os.path.join(output_root, record.name)
    os.makedirs(skill_dir, exist_ok=True)
    target = os.path.join(skill_dir, "SKILL.md")

    frontmatter = render_frontmatter(record, max_length)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(frontmatter)
        handle.write("\n\n")
        handle.write(record.body)
        handle.write("\n")
    return target


def copy_resources(record: SkillIR, output_root: str) -> list[str]:
    """Copy non-markdown resources (scripts, references subdirs) next to the skill.

    DSH resolves a skill's relative paths against the skill's base directory,
    so a skill that calls ``scripts/check_pdf_highlights.py`` needs that
    script present in the rendered tree.
    """
    source_dir = os.path.dirname(os.path.abspath(record.source))
    skill_dir = os.path.join(output_root, record.name)
    copied: list[str] = []

    for entry in sorted(os.listdir(source_dir)):
        if entry == "SKILL.md" or entry in CODEX_ONLY_FILES:
            continue
        source_path = os.path.join(source_dir, entry)
        target_path = os.path.join(skill_dir, entry)
        if os.path.isdir(source_path):
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            shutil.copytree(
                source_path,
                target_path,
                ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc", "node_modules"),
            )
            copied.append(entry)
        elif entry in ("package.json", "package-lock.json"):
            shutil.copy2(source_path, target_path)
            copied.append(entry)
    return copied


def render_all(records: list[SkillIR], output_root: str, max_length: int = CATALOG_DESCRIPTION_MAX_LENGTH) -> list[str]:
    """Render every record into ``output_root``, replacing it wholesale."""
    if os.path.isdir(output_root):
        shutil.rmtree(output_root)
    os.makedirs(output_root, exist_ok=True)

    written: list[str] = []
    for record in records:
        written.append(render_skill(record, output_root, max_length))
        copy_resources(record, output_root)
    return written
