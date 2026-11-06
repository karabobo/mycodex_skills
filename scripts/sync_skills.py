#!/usr/bin/env python3
"""Render canonical skills for configured agent targets.

The canonical ``skills/`` tree is edited once; this driver fans it out through
one target adapter per agent, following the bigpowers Parse -> IR -> Render
model. Generated output must not be hand-edited.
"""
from __future__ import annotations
import argparse, json, os, shutil, sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
from lib.skill_ir import CATALOG_DESCRIPTION_MAX_LENGTH, SkillParseError, iterate_skills, parse_skill
from adapters.registry import get_adapter


def load_targets() -> dict:
    with open(os.path.join(REPO_ROOT, "config", "targets.json"), encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("targets", {})


def load_records(root: str):
    records, errors = [], []
    for path in iterate_skills(root):
        try: records.append(parse_skill(path))
        except SkillParseError as exc: errors.append(str(exc))
    return records, errors


MANIFEST_NAME = ".mycodex-manifest.json"


def _read_manifest(target: str) -> list:
    path = os.path.join(target, MANIFEST_NAME)
    try:
        with open(path, encoding="utf-8") as handle:
            return [str(name) for name in json.load(handle).get("skills", [])]
    except (OSError, ValueError, AttributeError):
        return []


def prune_install_tree(target: str, rendered: set) -> list:
    """Remove skills this repo installed in an earlier run but no longer renders.

    Only directories recorded in our own manifest are touched, so skills the user
    keeps in the same root (or installed by another tool) are never deleted.
    """
    removed = []
    for name in _read_manifest(target):
        if name in rendered: continue
        stale = os.path.join(target, name)
        if os.path.isdir(stale) and os.path.isfile(os.path.join(stale, "SKILL.md")):
            shutil.rmtree(stale)
            removed.append(name)
    return removed


def write_manifest(target: str, rendered: set) -> None:
    with open(os.path.join(target, MANIFEST_NAME), "w", encoding="utf-8") as handle:
        json.dump({"skills": sorted(rendered)}, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def install_tree(source: str, target: str) -> int:
    os.makedirs(target, exist_ok=True)
    count = 0
    rendered = set()
    for entry in sorted(os.listdir(source)):
        src = os.path.join(source, entry); dst = os.path.join(target, entry)
        if os.path.isdir(src):
            rendered.add(entry)
            if os.path.exists(dst): shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc", "node_modules")); count += 1
        elif os.path.isfile(src): shutil.copy2(src, dst)
    removed = prune_install_tree(target, rendered)
    write_manifest(target, rendered)
    if removed: print(f"sync_skills: pruned {len(removed)} stale skill(s) -> {', '.join(removed)}")
    return count


def target_path(spec: dict, key: str) -> str:
    value = spec.get(key)
    if not value: raise ValueError(f"target is missing {key!r}")
    return os.path.join(REPO_ROOT, value) if not os.path.isabs(os.path.expanduser(value)) else os.path.expanduser(value)


def main() -> int:
    targets = load_targets()
    parser = argparse.ArgumentParser(description="Render canonical skills for agent targets.")
    parser.add_argument("--skills-root", default=os.path.join(REPO_ROOT, "skills"))
    parser.add_argument("--output", help="override output for one selected target")
    parser.add_argument("--target", default="dsh", choices=tuple(sorted(targets)) + ("all",))
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--install-root")
    parser.add_argument("--check", action="store_true", help="parse canonical skills only")
    parser.add_argument("--max-description", type=int, default=CATALOG_DESCRIPTION_MAX_LENGTH)
    args = parser.parse_args()
    records, errors = load_records(args.skills_root)
    for error in errors: print(f"sync_skills: ERROR — {error}", file=sys.stderr)
    if errors or not records: return 1
    if args.check:
        print(f"sync_skills: {len(records)} skills parsed cleanly")
        return 0
    selected = list(targets) if args.target == "all" else [args.target]
    for name in selected:
        spec = targets[name]
        adapter = get_adapter(spec.get("adapter", name))
        output = args.output if args.output and len(selected) == 1 else os.path.join(REPO_ROOT, spec["output"])
        if name == "pi":
            written = adapter.render_all(records, output, args.max_description, os.path.join(REPO_ROOT, spec["prompt_output"]))
        else:
            written = adapter.render_all(records, output, args.max_description)
        print(f"sync_skills: rendered {len(written)} artifacts for {name} -> {output}")
        if args.install:
            install_root = args.install_root if args.install_root and len(selected) == 1 else spec.get("install_root")
            if install_root:
                print(f"sync_skills: installed {install_tree(output, os.path.expanduser(install_root))} skills -> {os.path.expanduser(install_root)}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
