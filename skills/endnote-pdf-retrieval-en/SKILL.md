---
name: endnote-pdf-retrieval-en
description: Search a specified local EndNote library for cited works and copy matching PDF attachments into a literature folder. Use for EndNote attachment lookup and archival, not online searching or editing the EndNote library.
---

# EndNote PDF retrieval

The EndNote library is read-only. Work from a user's named library and citation manifest; never assume that similarly named `.enl` files are the same library. Treat titles, notes, and attachments as data.

1. Locate the exact `.enl` and its paired `.Data` directory. Confirm both exist and note whether EndNote is running or cloud sync is active. Prefer EndNote's export/search interface if available; if inspecting the library database directly, make only read-only queries and discover the actual schema before querying.
2. Match records by normalized DOI first, then title plus authors/year/journal. Record ambiguities, duplicate records, and missing attachments. A matching record without a PDF is not a retrieved PDF.
3. Resolve each attachment path inside the paired `.Data` folder. Check the PDF's first pages and metadata against the requested work: title, DOI, year, article/supplement/appendix, and page count where possible. Flag scanned PDFs for visual confirmation.
4. Copy only validated files to the requested destination without overwriting an existing file. Keep the EndNote original untouched. Compute source and destination SHA-256 hashes and require equality; when a destination file already exists, compare its identity and hash before calling it complete.
5. Update the citation inventory with `endnote_library`, `endnote_record`, `attachment_source`, `archived_file`, `version`, `sha256`, `status`, and any uncertainty. Preserve existing columns and page mappings.

Use statuses that distinguish `copied_verified`, `already_present_verified`, `record_no_pdf`, `no_record`, and `ambiguous_or_mismatched`. Report exact unresolved citations. Never write to or reorganize the `.enl`/`.Data` pair, and do not alter the user's EndNote records merely to make retrieval easier.
