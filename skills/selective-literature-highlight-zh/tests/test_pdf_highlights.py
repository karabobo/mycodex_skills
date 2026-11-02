"""Synthetic files only; no clinical or user documents are loaded."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

import fitz

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_pdf_highlights.py"
SPEC = importlib.util.spec_from_file_location("pdf_check", SCRIPT)
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class HighlightChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "source.pdf"
        self.output = Path(self.temp.name) / "output.pdf"
        with fitz.open() as doc:
            page = doc.new_page(width=400, height=400)
            page.insert_text((30, 50), "Synthetic cohort A: 12 of 40 responses at week 4.")
            doc.save(self.source)

    def produce(self, mutate=None, highlight=True):
        with fitz.open(self.source) as doc:
            page = doc[0]
            annot = None
            if highlight:
                annot = page.add_highlight_annot(page.search_for("12 of 40"))
                annot.set_info(content="", title="", subject="")
                annot.update()
            if mutate:
                mutate(doc, page, annot)
            doc.save(self.output)

    def check(self, expected=1, render=False):
        return CHECK.check_pdf(self.source, self.output, expected, render)

    def assert_error(self, fragment, result=None):
        result = result or self.check()
        self.assertFalse(result["passed"])
        self.assertTrue(any(fragment in x for x in result["errors"]), result)

    def test_valid_highlight(self):
        self.produce()
        result = self.check()
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["highlights"], 1)
        self.assertIn("claim_evidence_alignment", result["manual_checks_required"])

    def test_unchanged_pdf_render(self):
        self.output.write_bytes(self.source.read_bytes())
        result = self.check(expected=0, render=True)
        self.assertTrue(result["passed"], result)
        self.assertTrue(result["render_checked"])

    def test_each_comment_metadata_field(self):
        for field in ("content", "title", "subject"):
            with self.subTest(field=field):
                def mutate(doc, page, annot):
                    annot.set_info(**{field: "Unwanted annotation text"})
                    annot.update()
                self.produce(mutate)
                self.assert_error("comment_metadata")

    def test_popup(self):
        self.produce(lambda d, p, a: a.set_popup(fitz.Rect(100, 100, 200, 200)))
        self.assert_error("popup")

    def test_sticky_note(self):
        self.produce(lambda d, p, a: p.add_text_annot((100, 100), "Note"))
        self.assert_error("non_highlight_comment")

    def test_extra_page(self):
        self.produce(lambda d, p, a: d.new_page())
        self.assert_error("page_count_changed")

    def test_changed_body(self):
        self.produce(lambda d, p, a: p.insert_text((30, 100), "Changed content"))
        self.assert_error("text_changed")
        self.assert_error("content_stream_changed")

    def test_graphic_change_requires_render_review(self):
        # A graphic changes without changing extracted text.
        self.produce(lambda d, p, a: p.draw_rect(fitz.Rect(20, 120, 100, 150), fill=(1, 0, 0)))
        self.assert_error("render_diff_requires_review", self.check(render=True))

    def test_out_of_page_quad(self):
        self.produce(lambda d, p, a: p.add_highlight_annot(fitz.Rect(-20, 60, 20, 75)))
        self.assert_error("quad_outside_page", self.check(expected=2))

    def test_wrong_expected_count(self):
        self.produce()
        self.assert_error("highlight_count_mismatch", self.check(expected=2))

    def test_empty_requires_explicit_zero(self):
        self.produce(highlight=False)
        self.assert_error("no_highlights", self.check(expected=None))
        self.assertTrue(self.check(expected=0)["passed"])

    def test_rotated_page(self):
        with fitz.open(self.source) as doc:
            doc[0].set_rotation(90)
            data = doc.tobytes()
        self.source.write_bytes(data)
        self.produce()
        self.assertTrue(self.check()["passed"])


if __name__ == "__main__":
    unittest.main()
