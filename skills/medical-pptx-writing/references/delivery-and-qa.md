# Delivery and Quality Gates

## Separate review passes

1. **Medical:** concept, population, endpoint, statistics, source support, evidence boundary.
2. **Editorial:** terminology, grammar, translation, abbreviations, units, numerical consistency.
3. **Compliance:** label scope, unsupported superiority, absolute language, exploratory promotion, confidentiality.
4. **Visual:** hierarchy, readability, truthfulness, alignment, consistency, source readability.
5. **Editability:** native objects, chart data, tables, mechanisms, master/layout use, absence of flattening.

## Render verification

1. Inspect the PPTX structure and overflow/overlap results.
2. Render every slide.
3. Inspect every slide at full size; use montage only for flow and consistency.
4. Export native PDF and confirm visible output.
5. Recheck any slide changed after the last render.

Check:

- clipping, overlap, overflow, wrapping, missing fonts, broken glyphs;
- axes, legends, endpoints, denominators, CI, P values, risk tables, and citations;
- image sharpness, aspect ratio, and crop;
- consistent master, theme, title positions, spacing, and source format;
- object editability and source-file availability.

## Delivery package

- editable PPTX;
- final PDF;
- evidence/source manifest;
- claim ledger;
- storyline or slide blueprint when requested;
- version and data cutoff;
- review/change log;
- list of intentionally rasterized or partially editable components.

## Final QA prompt

> Perform final delivery QA on the medical PPTX. Review medical accuracy, wording, compliance boundary, visual integrity, and editability in separate passes. Render every slide and inspect it at full size. Verify axes, labels, denominators, statistics, citations, clipping, overlap, fonts, image quality, master consistency, and whether key content remains editable. Report unresolved evidence or editability limitations; do not claim completion if any requested slide remains unchecked.

