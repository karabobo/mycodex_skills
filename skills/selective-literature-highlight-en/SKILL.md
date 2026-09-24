---
name: selective-literature-highlight-en
description: Produce restrained, readable native PDF highlights for exact passages supporting a cited medical claim. Use for a focused paper-by-paper highlight package after source identity and claim support are checked; not for bulk decorative marking or full-deck audit.
---

# Selective literature highlights

Input: the exact displayed claim, citation/work ID, and candidate source PDF. Output: an unmodified original, a separately saved highlighted copy only when support is verified, and one ledger row per claim. For a full slide-by-slide claim audit, use `pdf-claim-highlighter-en`; this skill handles the focused annotation pass.

1. **Verify first.** Match visible PDF title, first author, year, DOI, and article-versus-supplement/version to the citation. Locate the exact result, definition, table cell, figure, or qualifying footnote that supports the claim. Record PDF page, printed page when different, and a short excerpt. If the work or support is uncertain, record the reason and leave it unhighlighted.
2. **Key.** Select the smallest evidence span that lets a reader verify the claim: usually a result sentence or relevant table cells, plus any qualifier that changes its meaning. Numbers without their population, denominator, endpoint, or time point are not enough.
3. **Concise and restrained.** Prefer a few short, editable native PDF Highlight annotations per claim. Avoid whole paragraphs, whole tables, opaque rectangles, repeated marking, and visual signals that imply the entire paper or recommendation is endorsed. Keep the original PDF untouched. For scanned pages, confirm visible words before placing a coordinate-based annotation.
4. **Visible.** Use a legible, low-opacity highlight (a muted gold around 0.3 opacity is a starting point, adjusted to the source and any user-provided sample). Do not hide text or table rules. Reopen and render the saved copy; inspect every annotated page at reading size, confirm page count and annotation placement, and ensure the copy opens in a standard PDF viewer.
5. Record `claim_id`, exact claim, work ID, source file/version and hash, PDF/printed page, excerpt/location, verdict, annotation count, highlighted-copy path, and caveat. Preserve source numbering and order when packaging multiple papers; reconcile ledger rows with actual files.

Use `supported`, `partially_supported`, `contradicted`, `not_found`, or `source_mismatch` as distinct verdicts. By default, create no highlighted copy for anything other than `supported`; explain unresolved or partially supported claims in the ledger. A highlight identifies a supporting passage, not the strength of a broader clinical recommendation.
