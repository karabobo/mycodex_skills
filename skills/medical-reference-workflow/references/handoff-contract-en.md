# Literature workflow handoff contract

Use this only when combining stages. Preserve an existing manifest's columns and row order; add a crosswalk or sidecar rather than rewriting a legacy sheet solely to fit this model.

## Identity

- **Work ID:** one cited publication or distinct version. Reuse it across metadata, EndNote, online, mutual-aid, and PDF checks.
- **Occurrence ID:** one appearance on one slide, linked to a work ID; keep slide number, exact displayed citation, and marker/location. Two occurrences may share a work ID.
- **Claim ID:** one checkable slide assertion, linked to its slide/occurrence and the work it cites. A compound assertion may yield several claim IDs.

Do not merge an abstract, full paper, supplement, or updated guideline merely because authors or topic match. When the identity is uncertain, use a provisional link and retain the competing candidates.

## Stage fields

Keep status fields separate: `metadata_status`, `endnote_status`, `online_status`, `pdf_status`, and `claim_verdict`. Never use a single “complete” flag to mean all five. Record DOI and title as verified values only after the metadata stage; keep printed DOI/title in raw fields. For an archived PDF, retain source kind, stable landing URL, version, file path, page count, and SHA-256. Source attempts may live in a separate log keyed by work ID; omit credentials, cookies, and expiring download links.

For a pre-existing row-per-citation CSV, its row number can be the occurrence ID. Add or map a stable work ID, including for duplicates, without discarding original columns. If the user asks for a new schema, a work table plus occurrence table is cleaner than repeating work metadata on every slide row.

## Completion checks

Reconcile counts separately: slide occurrences, distinct works, verified metadata, PDFs by source, unresolved works, claims by verdict, and highlighted copies. Every non-complete item needs a reason and next route. PDF possession is not claim support; a highlight is not proof unless its ledger identifies the exact supporting passage and qualifiers.
