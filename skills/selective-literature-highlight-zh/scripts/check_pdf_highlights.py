#!/usr/bin/env python3
"""Read-only checks for color-only PDF highlights; requires PyMuPDF.

Usage: python check_pdf_highlights.py SOURCE OUTPUT --expected-count 3 [--render]
Exit 0 means technical checks passed, not that evidence or wording is supported.
Existing navigation links/forms are not comment annotations and are not edited.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

import fitz


def check_pdf(source, output, expected_count=None, render=False):
    errors = []
    pages = []
    total = 0
    with fitz.open(source) as before, fitz.open(output) as after:
        if not before.is_pdf or not after.is_pdf:
            raise ValueError("Both inputs must be PDFs")
        if before.needs_pass or after.needs_pass:
            raise ValueError("Unlock authorized copies before checking")
        if len(before) != len(after):
            errors.append("page_count_changed")
        for index, page in enumerate(after):
            label = "page_%d" % (index + 1)
            if index < len(before):
                original = before[index]
                if original.rect != page.rect or original.rotation != page.rotation:
                    errors.append(label + ":geometry_changed")
                if original.get_text() != page.get_text():
                    errors.append(label + ":text_changed")
                if original.read_contents() != page.read_contents():
                    errors.append(label + ":content_stream_changed")
                if render:
                    a = original.get_pixmap(annots=False)
                    b = page.get_pixmap(annots=False)
                    if (a.width, a.height, a.samples) != (b.width, b.height, b.samples):
                        errors.append(label + ":render_diff_requires_review")
            count = 0
            # annot_xrefs also exposes standalone Popup objects excluded by annots().
            for _, kind, _ in page.annot_xrefs():
                if kind == fitz.PDF_ANNOT_POPUP:
                    errors.append(label + ":popup")
            for annot in page.annots() or []:
                if annot.type[0] != fitz.PDF_ANNOT_HIGHLIGHT:
                    errors.append(label + ":non_highlight_comment")
                    continue
                count += 1
                if any(annot.info.get(k, "") for k in ("content", "title", "subject")):
                    errors.append(label + ":comment_metadata")
                if annot.has_popup:
                    errors.append(label + ":popup")
                vertices = annot.vertices or []
                if not vertices or len(vertices) % 4:
                    errors.append(label + ":invalid_quads")
                    continue
                # Annotation coordinates are unrotated; do not reject valid rotated pages.
                bounds = page.rect * page.derotation_matrix
                for start in range(0, len(vertices), 4):
                    points = vertices[start:start + 4]
                    if not all(math.isfinite(value) for point in points for value in point):
                        errors.append(label + ":invalid_quads")
                        continue
                    quad = fitz.Quad(points)
                    if not quad.is_convex or quad.rect.is_empty:
                        errors.append(label + ":invalid_quads")
                    elif not (bounds + (-0.5, -0.5, 0.5, 0.5)).contains(quad.rect):
                        errors.append(label + ":quad_outside_page")
            total += count
            if count:
                pages.append({"page": index + 1, "highlights": count})
    if expected_count is not None and total != expected_count:
        errors.append("highlight_count_mismatch")
    if total == 0 and expected_count != 0:
        errors.append("no_highlights")
    return {
        "passed": not errors,
        "errors": sorted(set(errors)),
        "highlights": total,
        "marked_pages": pages,
        "output_sha256": hashlib.sha256(Path(output).read_bytes()).hexdigest(),
        "render_checked": render,
        "manual_checks_required": ["claim_evidence_alignment", "each_highlight_visual_review"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    if args.expected_count is not None and args.expected_count < 0:
        parser.error("--expected-count must be nonnegative")
    try:
        result = check_pdf(args.source, args.output, args.expected_count, args.render)
    except (OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"passed": False, "errors": [str(exc)]}))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
