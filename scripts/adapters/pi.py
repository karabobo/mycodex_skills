"""pi target renderer: skill directories plus prompt aliases."""
from __future__ import annotations
import os, shutil
from lib.skill_ir import SkillIR
from .target import render_skill_directory, render_prompt

def render_all(records: list[SkillIR], output_root: str, max_length: int = 0, prompt_output: str | None = None) -> list[str]:
    if os.path.isdir(output_root): shutil.rmtree(output_root)
    os.makedirs(output_root, exist_ok=True)
    written = [render_skill_directory(record, output_root, include_model=False) for record in records]
    if prompt_output:
        if os.path.isdir(prompt_output): shutil.rmtree(prompt_output)
        os.makedirs(prompt_output, exist_ok=True)
        written.extend(render_prompt(record, prompt_output) for record in records)
    return written
