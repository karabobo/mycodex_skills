#!/usr/bin/env python3
"""sync_skills.py — render the canonical skills/ tree for DeepSeek Harness.

Usage:
    python3 scripts/sync_skills.py                 # render into .dsh/skills
    python3 scripts/sync_skills.py --output DIR    # render somewhere else
    python3 scripts/sync_skills.py --install       # also sync into ~/.dsh/skills
    python3 scripts/sync_skills.py --check         # validate only, render nothing

The canonical tree in ``skills/`` stays Codex-flavoured source; this script
produces the DSH-flavoured rendering that DeepSeek Harness actually loads.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.join(SCRIPT_DIR, "lib"))

from lib.skill_ir import (  # noqa: E402
    CATALOG_DESCRIPTION_MAX_LENGTH,
    SkillParseError,
    iterate_skills,
    parse_skill,
)
from adapters.registry import get_adapter  # noqa: E402


def resolve_skills_root() -> str:
    return os.path.join(REPO_ROOT, "skills")


def resolve_default_output() -> str:
    return os.path.join(REPO_ROOT, ".dsh", "skills")


def resolve_user_install_root() -> str:
    """``~/.dsh/skills`` — the user-scoped DSH root (provider rank 400)."""
    home = os.environ.get("DSH_HOME")
    if not home:
        home = os.path.join(os.path.expanduser("~"), ".dsh")
    return os.path.join(home, "skills")


def load_records(skills_root: str) -> tuple[list, list[str]]:
    """Parse every skill. Returns (records, errors)."""
    records = []
    errors: list[str] = []
    for skill_md in iterate_skills(skills_root):
        try:
            records.append(parse_skill(skill_md))
        except SkillParseError as exc:
            errors.append(str(exc))
    return records, errors


def install_to(output_root: str, target_root: str) -> int:
    """Copy the rendered tree into a DSH skill root."""
    os.makedirs(target_root, exist_ok=True)
    installed = 0
    for entry in sorted(os.listdir(output_root)):
        source = os.path.join(output_root, entry)
        if not os.path.isdir(source):
            continue
        target = os.path.join(target_root, entry)
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(
            source,
            target,
            ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc"),
        )
        installed += 1
    return installed


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the canonical skills for DSH.")
    parser.add_argument("--skills-root", default=None, help="canonical skills directory")
    parser.add_argument("--output", default=None, help="rendered output directory")
    parser.add_argument("--install", action="store_true", help="also install into the selected target root")
    parser.add_argument("--install-root", default=None, help="override the install root")
    parser.add_argument("--target", choices=("dsh", "codex"), default="dsh", help="agent target adapter")
    parser.add_argument("--check", action="store_true", help="validate the canonical tree only")
    parser.add_argument(
        "--max-description",
        type=int,
        default=CATALOG_DESCRIPTION_MAX_LENGTH,
        help="description cap (DSH default: 500)",
    )
    args = parser.parse_args()

    skills_root = args.skills_root or resolve_skills_root()
    if args.output:
        output_root = args.output
    elif args.target == "dsh":
        output_root = resolve_default_output()
    else:
        output_root = os.path.join(REPO_ROOT, ".agents", args.target, "skills")

    adapter = get_adapter(args.target)

    records, errors = load_records(skills_root)
    for error in errors:
        print(f"sync_skills: ERROR — {error}", file=sys.stderr)
    if errors:
        return 1

    if not records:
        print(f"sync_skills: no skills found under {skills_root}", file=sys.stderr)
        return 1

    if args.check:
        print(f"sync_skills: {len(records)} skills parsed cleanly from {skills_root}")
        return 0

    written = adapter.render_all(records, output_root, args.max_description)
    print(f"sync_skills: rendered {len(written)} skills -> {output_root}")

    over = [r.name for r in records if len(r.description) > args.max_description]
    if over:
        print(
            f"sync_skills: NOTE — {len(over)} description(s) exceed {args.max_description} "
            f"characters and were rebalanced: {', '.join(over)}"
        )

    if args.install:
        target = args.install_root or resolve_user_install_root()
        count = install_to(output_root, target)
        print(f"sync_skills: installed {count} skills -> {target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
