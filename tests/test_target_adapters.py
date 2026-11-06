from __future__ import annotations
import os, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from adapters.registry import get_adapter
from sync_skills import install_tree
from lib.skill_ir import SkillIR

class TestTargetAdapters(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        source_dir = os.path.join(self.tmp.name, "source", "demo")
        os.makedirs(os.path.join(source_dir, "references"))
        self.source = os.path.join(source_dir, "SKILL.md")
        open(self.source, "w", encoding="utf-8").write("---\nname: demo\ndescription: Demo skill\n---\n\nBody\n")
        open(os.path.join(source_dir, "references", "note.md"), "w", encoding="utf-8").write("note")
        self.record = SkillIR("demo", "Demo skill", "Body", source=self.source)
    def tearDown(self): self.tmp.cleanup()
    def test_directory_targets_copy_resources(self):
        for name in ("codex", "cline", "gemini"):
            out = os.path.join(self.tmp.name, name)
            get_adapter(name).render_all([self.record], out)
            self.assertTrue(os.path.isfile(os.path.join(out, "demo", "SKILL.md")))
            self.assertTrue(os.path.isfile(os.path.join(out, "demo", "references", "note.md")))
    def test_cursor_rule_target(self):
        out = os.path.join(self.tmp.name, "cursor")
        get_adapter("cursor").render_all([self.record], out)
        self.assertTrue(os.path.isfile(os.path.join(out, "demo.mdc")))
    def test_pi_writes_skill_and_prompt(self):
        out, prompts = os.path.join(self.tmp.name, "pi"), os.path.join(self.tmp.name, "prompts")
        get_adapter("pi").render_all([self.record], out, prompt_output=prompts)
        self.assertTrue(os.path.isfile(os.path.join(out, "demo", "SKILL.md")))
        self.assertTrue(os.path.isfile(os.path.join(prompts, "demo.md")))
    def test_registry_has_initial_targets(self):
        for name in ("dsh", "codex", "cline", "cursor", "gemini", "pi"):
            self.assertIsNotNone(get_adapter(name))

    def test_install_tree_prunes_only_its_own_stale_skills(self):
        source = os.path.join(self.tmp.name, "rendered")
        os.makedirs(os.path.join(source, "demo"))
        open(os.path.join(source, "demo", "SKILL.md"), "w", encoding="utf-8").write("---\nname: demo\ndescription: Demo\n---\n\nBody\n")
        target = os.path.join(self.tmp.name, "installed")
        for name in ("demo", "old-pair-zh", "user-own"):
            os.makedirs(os.path.join(target, name))
            open(os.path.join(target, name, "SKILL.md"), "w", encoding="utf-8").write("x")
        manifest = os.path.join(target, ".mycodex-manifest.json")
        open(manifest, "w", encoding="utf-8").write('{"skills": ["demo", "old-pair-zh"]}\n')
        self.assertEqual(install_tree(source, target), 1)
        self.assertTrue(os.path.isdir(os.path.join(target, "demo")))
        self.assertFalse(os.path.exists(os.path.join(target, "old-pair-zh")))
        self.assertTrue(os.path.isdir(os.path.join(target, "user-own")), "never delete skills we did not install")
        self.assertEqual(sorted(os.listdir(target)), [".mycodex-manifest.json", "demo", "user-own"])

if __name__ == "__main__": unittest.main()
