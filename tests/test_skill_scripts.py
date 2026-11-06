"""Regression tests for the Node helper scripts shipped with individual skills.

These scripts are the executable part of the literature workflow: the Sci-Hub
fallback and the AbleSci headless/batch driver. Their unit-testable logic
(DOI normalisation, PDF validation, page counting, altcha proof-of-work) is
exposed through a ``--self-test`` mode so it can run without network access,
without a browser, and without a logged-in account.

The tests skip cleanly when Node.js is unavailable, matching how the rest of
this repository treats optional external tooling.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCIHUB_SCRIPT = os.path.join(ROOT, "skills", "literature-source-archive", "scripts", "scihub_fetch.mjs")
ABLESCI_SCRIPT = os.path.join(ROOT, "skills", "ablesci-literature-assist", "scripts", "ablesci_batch.mjs")
ABLESCI_SKILL_DIR = os.path.dirname(os.path.dirname(ABLESCI_SCRIPT))

NODE = shutil.which("node")


def run_node(script: str, *args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        [NODE, script, *args],
        cwd=os.path.dirname(script),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


@unittest.skipIf(NODE is None, "node is not installed")
class TestSciHubFetch(unittest.TestCase):
    def test_script_exists_and_parses(self):
        self.assertTrue(os.path.isfile(SCIHUB_SCRIPT))
        result = subprocess.run([NODE, "--check", SCIHUB_SCRIPT], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_self_test_reports_all_checks_passing(self):
        result = run_node(SCIHUB_SCRIPT, "--self-test")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"], payload)
        self.assertGreaterEqual(len(payload["checks"]), 9)


@unittest.skipIf(NODE is None, "node is not installed")
class TestAbleSciBatch(unittest.TestCase):
    def test_script_exists_and_parses(self):
        self.assertTrue(os.path.isfile(ABLESCI_SCRIPT))
        result = subprocess.run([NODE, "--check", ABLESCI_SCRIPT], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_self_test_reports_all_checks_passing(self):
        result = run_node(ABLESCI_SCRIPT, "--self-test")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"], payload)
        self.assertGreaterEqual(len(payload["checks"]), 6)

    def test_help_documents_safety_flags(self):
        result = run_node(ABLESCI_SCRIPT, "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for flag in ("--publish", "--accept", "--login", "--inspect", "--download"):
            self.assertIn(flag, result.stdout)

    def test_package_manifest_declares_playwright(self):
        manifest_path = os.path.join(ABLESCI_SKILL_DIR, "package.json")
        with open(manifest_path, encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertIn("playwright", manifest.get("dependencies", {}))
        self.assertEqual(manifest.get("type"), "module")


class TestLiteraturePolicyDocs(unittest.TestCase):
    """The Sci-Hub fallback must stay explicitly user-authorized in every doc."""

    def read(self, *parts: str) -> str:
        with open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
            return handle.read()

    def test_archive_skills_describe_authorized_scihub_fallback(self):
        merged = self.read("skills", "literature-source-archive", "SKILL.md")
        zh = en = merged
        self.assertIn("Sci-Hub", zh)
        self.assertIn("用户已授权", zh)
        self.assertIn("Authorized Sci-Hub fallback", en)
        # The old blanket prohibition must be gone.
        self.assertNotIn("不使用 Sci-Hub", zh)

    def test_endnote_miss_hands_off_to_archive_with_scihub(self):
        zh = self.read("skills", "endnote-pdf-retrieval", "SKILL.md")
        self.assertIn("literature-source-archive", zh)
        self.assertIn("unresolved_after_authorized_sources", zh)
        self.assertNotIn("不要使用 Sci-Hub", zh)

    def test_pptx_grouping_rule_is_not_inverted(self):
        pptx = self.read("skills", "medical-pptx-writing", "SKILL.md")
        workflow = self.read("skills", "medical-reference-workflow", "SKILL.md")
        for text in (pptx, workflow):
            self.assertNotIn("必须保持**不可组合**", text)
        self.assertIn("noGrp", pptx)
        self.assertIn("nlm_short.ens", pptx)
        self.assertIn("noGrp", workflow)
        self.assertIn("nlm_short.ens", workflow)

    def test_pptx_forbids_hedging_and_disclaimers(self):
        pptx = self.read("skills", "medical-pptx-writing", "SKILL.md")
        claims = self.read("skills", "medical-pptx-writing", "references", "evidence-and-claims.md")
        self.assertIn("No defensive hedging, no disclaimers, no extrapolation", pptx)
        self.assertIn("## Forbidden slide wording", claims)
        for banned in ("不能证明", "不足以说明", "并非", "而不是", "尚不能", "更准确地说",
                       "仅供参考", "仅供内部使用", "尚需进一步验证", "class effect"):
            self.assertIn(banned, claims)

    def test_pptx_ships_page_recipes(self):
        pptx = self.read("skills", "medical-pptx-writing", "SKILL.md")
        kit = self.read("skills", "medical-pptx-writing", "references", "page-kit.md")
        self.assertIn("references/page-kit.md", pptx)
        self.assertIn("## Page recipes", pptx)
        for page in ("封面", "章节页", "疾病负担", "未满足需求", "机制", "关键研究设计",
                     "疗效主图", "亚组与人群", "安全性", "指南与定位", "对比",
                     "临床落地", "总结"):
            self.assertIn(page, kit)
        self.assertIn("数字三件套", kit)
        self.assertIn("一句话临床含义", kit)
        self.assertIn("标题怎么写", kit)
        self.assertIn("结论标题", kit)
        self.assertIn("只读标题", kit)
        self.assertIn("Action titles", kit)
        # The five MBB action-title rules and the two hard constraints stay explicit.
        for rule in ("五条硬规则", "完整句子", "15 词", "主动语态", "带数字", "放不下就拆页", "永不缩字号"):
            self.assertIn(rule, kit)
        for rule in ("**Title rules.**", "complete sentence", "15 words", "active voice",
                     "never shrink the font"):
            self.assertIn(rule, pptx)

    def test_pptx_font_and_size_defaults(self):
        pptx = self.read("skills", "medical-pptx-writing", "SKILL.md")
        visual = self.read("skills", "medical-pptx-writing", "references", "visual-and-editable-production.md")
        for text in (pptx, visual):
            self.assertIn("微软雅黑", text)
            self.assertIn("Arial", text)
        self.assertIn("<a:ea typeface=\"微软雅黑\"/>", visual)
        # The reference list defaults to 8 pt, not the older 6-8 pt range.
        self.assertIn("8 pt", pptx)
        self.assertNotIn("6–8 pt", visual)
        # Titles default to 24 pt inside a 20-32 pt band.
        self.assertIn("24 pt", pptx)
        self.assertIn("20–32 pt", pptx)
        self.assertIn("24 pt", visual)
        self.assertIn("20–32 pt", visual)
        workflow = self.read("skills", "medical-reference-workflow", "SKILL.md")
        zh_part, en_part = workflow.split("## English", 1)
        for part in (zh_part, en_part):
            self.assertIn("微软雅黑", part)
            self.assertIn("Arial", part)

    def test_skills_are_single_bilingual_documents(self):
        names = sorted(n for n in os.listdir(os.path.join(ROOT, "skills"))
                       if os.path.isdir(os.path.join(ROOT, "skills", n)) and not n.startswith("."))
        self.assertEqual(len(names), 10, names)
        for name in names:
            self.assertFalse(name.endswith(("-zh", "-en")), name)
        for name in ("bibliographic-metadata-resolver", "endnote-pdf-retrieval",
                     "literature-source-archive", "medical-reference-workflow",
                     "pdf-claim-highlighter", "pptx-citation-inventory",
                     "selective-literature-highlight", "ablesci-literature-assist"):
            text = self.read("skills", name, "SKILL.md")
            self.assertIn("## 中文", text, name)
            self.assertIn("## English", text, name)
            self.assertIn(f"name: {name}", text, name)


if __name__ == "__main__":
    unittest.main()
