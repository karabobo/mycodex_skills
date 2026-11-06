#!/usr/bin/env python3
"""Tests for the DSH adapter.

These lock the behaviour that the DeepSeek Harness contract demands. The
expected values are taken from the DSH source, not from this
implementation's current output:

- name grammar: ``^[a-z0-9]+(?:-[a-z0-9]+)*$`` (dsh-skill.js)
- description normalization and truncation (dsh-tool-skill.js):
    normalized = value.replaceAll(/\\s+/g, " ").trim()
    normalized.length <= max ? normalized : `${normalized.slice(0, max - 3)}...`
- legacy frontmatter keys are rejected (dsh-skill-filesystem)
- required frontmatter is ``name`` + ``description``

Run:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "lib"))

from adapters.dsh import _rebalance_description, _split_description, render_all  # noqa: E402
from lib.skill_ir import (  # noqa: E402
    CATALOG_DESCRIPTION_MAX_LENGTH,
    SkillParseError,
    normalize_description,
    parse_skill,
    truncate_description,
)

SKILLS_ROOT = os.path.join(REPO_ROOT, "skills")


def write_skill(directory: str, name: str, frontmatter: str, body: str = "# Body\n") -> str:
    """Write a SKILL.md into ``<directory>/<name>/SKILL.md`` and return its path."""
    skill_dir = os.path.join(directory, name)
    os.makedirs(skill_dir, exist_ok=True)
    path = os.path.join(skill_dir, "SKILL.md")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"---\n{frontmatter}---\n\n{body}")
    return path


class TestDescriptionContract(unittest.TestCase):
    def test_normalization_matches_dsh(self):
        self.assertEqual(normalize_description("  a\n b\tc  "), "a b c")

    def test_truncation_matches_dsh(self):
        value = "x" * 600
        self.assertEqual(len(truncate_description(value)), CATALOG_DESCRIPTION_MAX_LENGTH)
        self.assertTrue(truncate_description(value).endswith("..."))
        self.assertEqual(truncate_description(value)[: CATALOG_DESCRIPTION_MAX_LENGTH - 3], "x" * 497)

    def test_short_description_is_untouched(self):
        self.assertEqual(truncate_description("short"), "short")

    def test_overlong_description_is_rebalanced_not_truncated(self):
        """The scope clause must survive — losing it misroutes the model."""
        description = (
            "Use only for English-language AbleSci literature mutual-aid workflows: "
            "submitting one English DOI/article at a time, handling existing uploaded "
            "requests before new submissions, verifying extracted English article "
            "metadata, opening assist details, downloading uploaded PDF files through "
            "normal nodes, saving and validating PDFs, and optionally using macOS "
            "Keychain-stored AbleSci credentials without exposing passwords to anyone. "
            "Do not use this skill for Chinese-language or other non-English literature."
        )
        self.assertGreater(len(description), CATALOG_DESCRIPTION_MAX_LENGTH)
        result = _rebalance_description(description, CATALOG_DESCRIPTION_MAX_LENGTH)

        self.assertLessEqual(len(result), CATALOG_DESCRIPTION_MAX_LENGTH)
        self.assertIn("Do not use this skill for Chinese-language or other non-English literature.", result)
        # The head of the positive clause must survive too.
        self.assertTrue(result.startswith("Use only for English-language AbleSci"))

    def test_split_description_finds_negative_scope(self):
        primary, negative = _split_description(
            "Do useful things with PDFs. Do not use this skill for scanned books."
        )
        self.assertEqual(primary, "Do useful things with PDFs.")
        self.assertEqual(negative, "Do not use this skill for scanned books.")

    def test_split_description_without_negative_clause(self):
        primary, negative = _split_description("Only does one thing well.")
        self.assertEqual(negative, "")
        self.assertEqual(primary, "Only does one thing well.")


class TestFrontmatterParsing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_parses_name_and_description(self):
        path = write_skill(self.tmp, "demo-skill", "name: demo-skill\ndescription: A demo skill.\n")
        record = parse_skill(path)
        self.assertEqual(record.name, "demo-skill")
        self.assertEqual(record.description, "A demo skill.")

    def test_rejects_missing_description(self):
        path = write_skill(self.tmp, "demo-skill", "name: demo-skill\n")
        with self.assertRaises(SkillParseError):
            parse_skill(path)

    def test_rejects_missing_name(self):
        path = write_skill(self.tmp, "demo-skill", "description: A demo skill.\n")
        with self.assertRaises(SkillParseError):
            parse_skill(path)

    def test_rejects_invalid_name_grammar(self):
        path = write_skill(self.tmp, "Demo_Skill", "name: Demo_Skill\ndescription: x\n")
        with self.assertRaises(SkillParseError):
            parse_skill(path)

    def test_rejects_missing_frontmatter(self):
        path = os.path.join(self.tmp, "raw.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("# no frontmatter\n")
        with self.assertRaises(SkillParseError):
            parse_skill(path)

    def test_parses_when_to_use(self):
        path = write_skill(
            self.tmp,
            "demo-skill",
            "name: demo-skill\ndescription: A demo skill.\nwhenToUse: When the user asks for a demo.\n",
        )
        record = parse_skill(path)
        self.assertEqual(record.when_to_use, "When the user asks for a demo.")

    def test_parses_invocation_policy(self):
        path = write_skill(
            self.tmp,
            "demo-skill",
            "name: demo-skill\ndescription: A demo skill.\n"
            "disable-model-invocation: true\nuser-invocable: false\n",
        )
        record = parse_skill(path)
        self.assertTrue(record.disable_model_invocation)
        self.assertFalse(record.user_invocable)

    def test_quoted_description_is_unquoted(self):
        path = write_skill(self.tmp, "demo-skill", 'name: demo-skill\ndescription: "A \\"quoted\\" demo."\n')
        record = parse_skill(path)
        self.assertEqual(record.description, 'A "quoted" demo.')

    def test_sibling_markdown_is_folded_into_body(self):
        path = write_skill(self.tmp, "demo-skill", "name: demo-skill\ndescription: A demo skill.\n")
        with open(os.path.join(os.path.dirname(path), "REFERENCE.md"), "w", encoding="utf-8") as handle:
            handle.write("# Reference\n")
        record = parse_skill(path)
        self.assertIn("# Reference", record.body)


class TestRenderedTree(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.src = os.path.join(self.tmp, "src")
        self.out = os.path.join(self.tmp, "out")
        os.makedirs(self.src)

    def test_renders_directory_bundle(self):
        write_skill(self.src, "demo-skill", "name: demo-skill\ndescription: A demo skill.\n")
        records = [parse_skill(os.path.join(self.src, "demo-skill", "SKILL.md"))]
        render_all(records, self.out)
        self.assertTrue(os.path.isfile(os.path.join(self.out, "demo-skill", "SKILL.md")))

    def test_strips_codex_only_agents_dir(self):
        skill_dir = os.path.join(self.src, "demo-skill")
        write_skill(self.src, "demo-skill", "name: demo-skill\ndescription: A demo skill.\n")
        os.makedirs(os.path.join(skill_dir, "agents"), exist_ok=True)
        with open(os.path.join(skill_dir, "agents", "openai.yaml"), "w", encoding="utf-8") as handle:
            handle.write("name: Demo\n")
        records = [parse_skill(os.path.join(skill_dir, "SKILL.md"))]
        render_all(records, self.out)
        self.assertFalse(os.path.exists(os.path.join(self.out, "demo-skill", "agents")))

    def test_copies_script_resources(self):
        skill_dir = os.path.join(self.src, "demo-skill")
        write_skill(self.src, "demo-skill", "name: demo-skill\ndescription: A demo skill.\n")
        os.makedirs(os.path.join(skill_dir, "scripts"), exist_ok=True)
        with open(os.path.join(skill_dir, "scripts", "run.py"), "w", encoding="utf-8") as handle:
            handle.write("print('hi')\n")
        records = [parse_skill(os.path.join(skill_dir, "SKILL.md"))]
        render_all(records, self.out)
        self.assertTrue(os.path.isfile(os.path.join(self.out, "demo-skill", "scripts", "run.py")))

    def test_copies_reference_subdirectories(self):
        skill_dir = os.path.join(self.src, "demo-skill")
        write_skill(self.src, "demo-skill", "name: demo-skill\ndescription: A demo skill.\n")
        os.makedirs(os.path.join(skill_dir, "references"), exist_ok=True)
        with open(os.path.join(skill_dir, "references", "contract.md"), "w", encoding="utf-8") as handle:
            handle.write("# Contract\n")
        records = [parse_skill(os.path.join(skill_dir, "SKILL.md"))]
        render_all(records, self.out)
        self.assertTrue(os.path.isfile(os.path.join(self.out, "demo-skill", "references", "contract.md")))

    def test_emits_when_to_use(self):
        write_skill(
            self.src,
            "demo-skill",
            "name: demo-skill\ndescription: A demo skill.\nwhenToUse: Use for demos.\n",
        )
        records = [parse_skill(os.path.join(self.src, "demo-skill", "SKILL.md"))]
        render_all(records, self.out)
        with open(os.path.join(self.out, "demo-skill", "SKILL.md"), encoding="utf-8") as handle:
            rendered = handle.read()
        self.assertIn("whenToUse:", rendered)

    def test_emits_invocation_policy(self):
        write_skill(
            self.src,
            "demo-skill",
            "name: demo-skill\ndescription: A demo skill.\n"
            "disable-model-invocation: true\nuser-invocable: false\n",
        )
        records = [parse_skill(os.path.join(self.src, "demo-skill", "SKILL.md"))]
        render_all(records, self.out)
        with open(os.path.join(self.out, "demo-skill", "SKILL.md"), encoding="utf-8") as handle:
            rendered = handle.read()
        self.assertIn("disable-model-invocation: true", rendered)
        self.assertIn("user-invocable: false", rendered)

    def test_does_not_emit_legacy_keys(self):
        write_skill(self.src, "demo-skill", "name: demo-skill\ndescription: A demo skill.\n")
        records = [parse_skill(os.path.join(self.src, "demo-skill", "SKILL.md"))]
        render_all(records, self.out)
        with open(os.path.join(self.out, "demo-skill", "SKILL.md"), encoding="utf-8") as handle:
            rendered = handle.read()
        for legacy in ("disableModelInvocation", "modelInvocable", "userInvocable"):
            self.assertNotIn(legacy, rendered)


class TestCanonicalRepo(unittest.TestCase):
    """The real skill tree must satisfy the DSH contract."""

    def test_every_canonical_skill_parses(self):
        from lib.skill_ir import iterate_skills

        found = iterate_skills(SKILLS_ROOT)
        self.assertGreater(len(found), 0)
        for path in found:
            record = parse_skill(path)
            self.assertTrue(record.name)
            self.assertTrue(record.description)

    def test_rendered_tree_passes_validation(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
        from validate_dsh_skills import validate_tree

        rendered_root = os.path.join(REPO_ROOT, ".dsh", "skills")
        if not os.path.isdir(rendered_root):
            self.skipTest(".dsh/skills not rendered yet")
        report = validate_tree(rendered_root)
        self.assertEqual(report.errors, [], f"errors: {report.errors}")


if __name__ == "__main__":
    unittest.main()
