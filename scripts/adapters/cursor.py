"""Cursor target renderer."""
from __future__ import annotations
import os, shutil
from lib.skill_ir import SkillIR
from .target import render_rule_file

def render_all(records: list[SkillIR], output_root: str, max_length: int = 0) -> list[str]:
    if os.path.isdir(output_root): shutil.rmtree(output_root)
    os.makedirs(output_root, exist_ok=True)
    return [render_rule_file(record, output_root) for record in records]
