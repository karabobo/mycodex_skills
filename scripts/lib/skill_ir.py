#!/usr/bin/env python3
"""Skill IR parser — canonical SKILL.md -> platform-neutral intermediate record.

The IR is the single contract between the canonical ``skills/`` tree and every
rendered target. A renderer never re-parses YAML; it only reads fields from
this record, so adding a target never means touching the parser.

Mirrors the bigpowers Parse->IR->Render architecture, reduced to the fields
DeepSeek Harness actually consumes.

Fields
------
name          str   skill name (DSH grammar: ^[a-z0-9]+(?:-[a-z0-9]+)*$)
description   str   catalog description
when_to_use   str   optional trigger hint (DSH renders this in the catalog)
body          str   markdown body, frontmatter stripped
model         str   optional model hint
effort        str   optional effort hint
disable_model_invocation  bool
user_invocable           bool
source       str   path of the SKILL.md this came from
"""

from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass, field

# DSH's skill-name grammar, verbatim from dsh-skill.js:
#   const SKILL_NAME = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# dsh-tool-skill.js caps catalog descriptions at 500 normalized characters.
CATALOG_DESCRIPTION_MAX_LENGTH = 500

_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.S)


class SkillParseError(Exception):
    """Raised when a SKILL.md cannot be turned into an IR record."""


@dataclass
class SkillIR:
    name: str
    description: str
    body: str
    when_to_use: str = ""
    model: str = ""
    effort: str = ""
    disable_model_invocation: bool = False
    user_invocable: bool = True
    source: str = ""
    extra_files: list[str] = field(default_factory=list)


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_raw, body). Frontmatter may be absent."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return "", text
    return match.group(1), text[match.end():]


def _parse_scalar(raw: str) -> str:
    """Decode a YAML scalar into a plain string.

    Handles the single-quoted, double-quoted and plain forms that skill
    frontmatter actually uses. Block scalars (| and >) are folded into a
    single space because DSH normalizes whitespace in descriptions anyway.
    """
    value = raw.strip()
    if not value:
        return ""
    if value[0] in "|>":
        # Block scalar indicator — the folded content is on following lines.
        return ""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        inner = value[1:-1]
        if value[0] == '"':
            return inner.replace('\\"', '"').replace("\\\\", "\\")
        return inner.replace("''", "'")
    # Strip trailing comment on a plain scalar ("value # note").
    comment = re.search(r"\s+#\s", value)
    if comment:
        value = value[: comment.start()]
    return value.strip()


def _parse_frontmatter(raw: str) -> dict[str, str]:
    """Parse the frontmatter block into a flat string->string mapping.

    Deliberately minimal: the skill frontmatter schema is a flat set of
    scalars, so a full YAML parser would add a dependency for no gain (the
    repo must stay installable on a stock Python 3).
    """
    fields: dict[str, str] = {}
    pending_key: str | None = None
    pending_parts: list[str] = []

    def flush() -> None:
        nonlocal pending_key, pending_parts
        if pending_key is not None:
            joined = " ".join(part.strip() for part in pending_parts if part.strip())
            fields[pending_key] = joined.strip()
        pending_key = None
        pending_parts = []

    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        # A more-indented line continues the previous key.
        if line[:1] in (" ", "\t") and pending_key is not None:
            pending_parts.append(line)
            continue
        key_match = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if not key_match:
            continue
        flush()
        key = key_match.group(1).strip()
        value = key_match.group(2)
        if value.strip() in ("|", ">", "|-", ">-", "|+", ">+"):
            pending_key = key
            pending_parts = []
            continue
        fields[key] = _parse_scalar(value)
    flush()
    return fields


def _as_bool(value: str, default: bool) -> bool:
    """DSH accepts true/false/yes/no/on/off/1/0 for boolean frontmatter."""
    if value == "":
        return default
    lowered = value.strip().lower()
    if lowered in ("true", "yes", "on", "1"):
        return True
    if lowered in ("false", "no", "off", "0"):
        return False
    raise SkillParseError(f"frontmatter boolean must be a boolean, got {value!r}")


def _collect_body(body: str, skill_dir: str) -> tuple[str, list[str]]:
    """Body plus any sibling markdown files, appended in stable order.

    DSH resolves a skill's resources against the skill's base directory, so a
    sibling ``REFERENCE.md`` is legitimate context and is folded into the
    body the same way bigpowers does it.
    """
    extras = sorted(
        path
        for path in glob.glob(os.path.join(skill_dir, "*.md"))
        if os.path.basename(path) != "SKILL.md"
    )
    parts = [body.strip()]
    for path in extras:
        with open(path, "r", encoding="utf-8") as handle:
            parts.append(handle.read().strip())
    return "\n\n---\n\n".join(part for part in parts if part), [os.path.basename(p) for p in extras]


def parse_skill(skill_md_path: str) -> SkillIR:
    """Parse one SKILL.md into a SkillIR record."""
    if not os.path.isfile(skill_md_path):
        raise SkillParseError(f"file not found: {skill_md_path}")

    with open(skill_md_path, "r", encoding="utf-8") as handle:
        text = handle.read()

    raw_frontmatter, raw_body = _split_frontmatter(text)
    if not raw_frontmatter.strip():
        raise SkillParseError(f"missing YAML frontmatter: {skill_md_path}")

    fields = _parse_frontmatter(raw_frontmatter)

    name = fields.get("name", "")
    if not name:
        raise SkillParseError(f"frontmatter is missing 'name': {skill_md_path}")
    if not SKILL_NAME_RE.match(name):
        raise SkillParseError(
            f"skill name {name!r} does not match DSH grammar "
            f"^[a-z0-9]+(?:-[a-z0-9]+)*$: {skill_md_path}"
        )

    description = fields.get("description", "")
    if not description:
        raise SkillParseError(f"frontmatter is missing 'description': {skill_md_path}")

    skill_dir = os.path.dirname(os.path.abspath(skill_md_path))
    body, extras = _collect_body(raw_body, skill_dir)

    return SkillIR(
        name=name,
        description=description,
        body=body,
        when_to_use=fields.get("whenToUse", ""),
        model=fields.get("model", ""),
        effort=fields.get("effort", ""),
        disable_model_invocation=_as_bool(fields.get("disable-model-invocation", ""), False),
        user_invocable=_as_bool(fields.get("user-invocable", ""), True),
        source=skill_md_path,
        extra_files=extras,
    )


def iterate_skills(skills_root: str) -> list[str]:
    """List every ``<skills_root>/<name>/SKILL.md`` in stable sorted order."""
    if not os.path.isdir(skills_root):
        return []
    found = []
    for entry in sorted(os.listdir(skills_root)):
        skill_dir = os.path.join(skills_root, entry)
        if os.path.isdir(skill_dir):
            skill_md = os.path.join(skill_dir, "SKILL.md")
            if os.path.isfile(skill_md):
                found.append(skill_md)
    return found


def normalize_description(value: str) -> str:
    """Match DSH's own normalization exactly.

    dsh-tool-skill.js:
        const normalized = value.replaceAll(/\\s+/g, " ").trim();
    """
    return re.sub(r"\s+", " ", value).strip()


def truncate_description(value: str, max_length: int = CATALOG_DESCRIPTION_MAX_LENGTH) -> str:
    """Match DSH's own truncation exactly.

    dsh-tool-skill.js:
        return normalized.length <= maxLength
            ? normalized
            : `${normalized.slice(0, maxLength - 3)}...`;
    """
    normalized = normalize_description(value)
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 3] + "..."


def yaml_quote(value: str) -> str:
    """Emit a YAML double-quoted scalar that survives DSH's YAML parser."""
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", " ")
        .replace("\n", " ")
    )
    return f'"{escaped}"'
