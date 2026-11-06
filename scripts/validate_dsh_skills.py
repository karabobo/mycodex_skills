#!/usr/bin/env python3
"""validate_dsh_skills.py — check a skill tree against the DSH loading contract.

This is the DSH equivalent of a linter. It encodes the rules taken from the
DeepSeek Harness source, so a skill that would silently fail to load (or
load with a mangled description) is caught before it reaches the catalog.

Rules checked
-------------
R1  Each skill is a directory ``<root>/<name>/`` containing ``SKILL.md``.
    Nested ``**/SKILL.md`` is NOT discovered by DSH.
R2  ``name`` matches ``^[a-z0-9]+(?:-[a-z0-9]+)*$`` and equals the directory
    name (DSH resolves the skill by its frontmatter name).
R3  ``name`` and ``description`` are present.
R4  ``description`` is at most 500 normalized characters — DSH truncates the
    catalog entry otherwise, cutting scope clauses mid-sentence.
R5  No legacy frontmatter keys (``disableModelInvocation``,
    ``modelInvocable``, ``userInvocable``) — DSH throws on these.
R6  Invocation-policy booleans are real booleans.
R7  Every relative path referenced from the body resolves inside the skill
    directory.
R8  No leftover Codex-only artifacts (``agents/openai.yaml``).

Usage:
    python3 scripts/validate_dsh_skills.py            # validate .dsh/skills
    python3 scripts/validate_dsh_skills.py DIR        # validate another tree
    python3 scripts/validate_dsh_skills.py --strict   # warnings become errors
"""

from __future__ import annotations

import argparse
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(SCRIPT_DIR, "lib"))

from lib.skill_ir import (  # noqa: E402
    CATALOG_DESCRIPTION_MAX_LENGTH,
    SKILL_NAME_RE,
    normalize_description,
)

LEGACY_KEYS = ("disableModelInvocation", "modelInvocable", "userInvocable")
LEGACY_RE = re.compile(r"^(?:%s)\s*:" % "|".join(LEGACY_KEYS), re.M)
BOOLEAN_KEYS = ("disable-model-invocation", "user-invocable")
LINK_RE = re.compile(r"\]\(([^)\s]+)")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.S)


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def _split_frontmatter(text: str) -> tuple[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return "", text
    return match.group(1), text[match.end():]


def _field(raw: str, key: str) -> str:
    match = re.search(r"^%s\s*:\s*(.*)$" % re.escape(key), raw, re.M)
    if not match:
        return ""
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        inner = value[1:-1]
        if value[0] == '"':
            return inner.replace('\\"', '"').replace("\\\\", "\\")
        return inner.replace("''", "'")
    return value


def validate_tree(root: str) -> Report:
    report = Report()

    if not os.path.isdir(root):
        report.error(f"{root}: skill root does not exist")
        return report

    # R1 — a nested SKILL.md is not discovered by DSH.
    for dirpath, _dirnames, filenames in os.walk(root):
        if "SKILL.md" in filenames and dirpath != root:
            depth = os.path.relpath(dirpath, root).count(os.sep)
            if depth >= 1:
                report.error(
                    f"{os.path.relpath(dirpath, root)}: nested SKILL.md is not discovered by DSH "
                    "(fold the content into the top-level skill body)"
                )

    skill_dirs = [
        os.path.join(root, entry)
        for entry in sorted(os.listdir(root))
        if os.path.isdir(os.path.join(root, entry))
    ]
    if not skill_dirs:
        report.warn(f"{root}: no skill directories found")

    for skill_dir in skill_dirs:
        dir_name = os.path.basename(skill_dir)
        skill_md = os.path.join(skill_dir, "SKILL.md")

        if not os.path.isfile(skill_md):
            report.error(f"{dir_name}: missing SKILL.md")
            continue

        with open(skill_md, "r", encoding="utf-8") as handle:
            text = handle.read()

        raw, body = _split_frontmatter(text)
        if not raw.strip():
            report.error(f"{dir_name}: missing YAML frontmatter")
            continue

        # R5 — legacy keys make DSH throw and skip the skill entirely.
        legacy = LEGACY_RE.search(raw)
        if legacy:
            report.error(
                f"{dir_name}: legacy frontmatter key {legacy.group(0)[:-1]!r} is rejected by DSH "
                "(use the kebab-case canonical key)"
            )

        name = _field(raw, "name")
        description = _field(raw, "description")

        # R3
        if not name:
            report.error(f"{dir_name}: frontmatter is missing 'name'")
        if not description:
            report.error(f"{dir_name}: frontmatter is missing 'description'")

        # R2
        if name:
            if not SKILL_NAME_RE.match(name):
                report.error(
                    f"{dir_name}: name {name!r} does not match DSH grammar "
                    "^[a-z0-9]+(?:-[a-z0-9]+)*$"
                )
            if name != dir_name:
                report.error(f"{dir_name}: frontmatter name {name!r} != directory name")

        # R4
        if description:
            normalized = normalize_description(description)
            if len(normalized) > CATALOG_DESCRIPTION_MAX_LENGTH:
                report.error(
                    f"{dir_name}: description is {len(normalized)} characters; DSH truncates the "
                    f"catalog at {CATALOG_DESCRIPTION_MAX_LENGTH} "
                    f"-> {normalized[: CATALOG_DESCRIPTION_MAX_LENGTH - 3]}..."
                )

        # R6
        for key in BOOLEAN_KEYS:
            value = _field(raw, key)
            if value and value.lower() not in ("true", "false", "yes", "no", "on", "off", "1", "0"):
                report.error(f"{dir_name}: {key} must be a boolean, got {value!r}")

        # R7 — relative links must resolve inside the skill directory.
        for target in LINK_RE.findall(body):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path_part = target.split("#", 1)[0]
            if not path_part:
                continue
            resolved = os.path.normpath(os.path.join(skill_dir, path_part))
            if not os.path.exists(resolved):
                report.error(f"{dir_name}: referenced path does not exist: {target}")

        # R8
        codex_meta = os.path.join(skill_dir, "agents", "openai.yaml")
        if os.path.exists(codex_meta):
            report.warn(
                f"{dir_name}: agents/openai.yaml is Codex-only and is ignored by DSH"
            )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a skill tree against the DSH contract.")
    parser.add_argument(
        "root",
        nargs="?",
        default=os.path.join(REPO_ROOT, ".dsh", "skills"),
        help="skill root to validate",
    )
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = parser.parse_args()

    report = validate_tree(args.root)

    for warning in report.warnings:
        print(f"WARN  {warning}")
    for error in report.errors:
        print(f"ERROR {error}")

    if report.errors:
        print(f"\nvalidate_dsh_skills: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
        return 1
    if args.strict and report.warnings:
        print(f"\nvalidate_dsh_skills: {len(report.warnings)} warning(s) (strict)")
        return 1

    print(f"\nvalidate_dsh_skills: OK — {args.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
