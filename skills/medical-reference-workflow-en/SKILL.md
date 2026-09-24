---
name: medical-reference-workflow-en
description: "Coordinate an English-language medical slide literature request across PPTX citations, DOI metadata, local EndNote, online PDFs, optional AbleSci, and claim-level highlighting."
---

# Medical reference workflow

Use this when the user asks for the whole chain. Invoke the component skills only for requested stages; a request to collect PDFs does not itself authorize claim-level review, posting a mutual-aid request, or accepting a submitted file.

When two or more stages exchange a manifest, read [references/handoff-contract.md](references/handoff-contract.md) before editing it. The contract distinguishes a work from each slide occurrence and each claim; it does not require replacing the user's existing spreadsheet.

| Stage | Skill | Handoff condition |
| --- | --- | --- |
| Slide citation inventory | `pptx-citation-inventory-en` | Every rendered slide checked; raw citations and repeat occurrences retained |
| DOI and metadata resolution | `bibliographic-metadata-resolver-en` | Every work has a verified identity or a documented unresolved reason |
| Local EndNote lookup | `endnote-pdf-retrieval-en` | Named library searched read-only; copied files hash-verified |
| Online source acquisition | `literature-source-archive-en` | Unresolved works checked across lawful sources; each attempt and verified PDF attributed |
| English mutual aid, when requested | `ablesci-literature-assist` | One DOI at a time; metadata and downloaded file verified before acceptance |
| Full slide claim audit, when requested | `pdf-claim-highlighter-en` | Every in-scope claim has a verdict and source location |
| Focused literature highlights, when requested | `selective-literature-highlight-en` | Only supported passages marked; annotated copies reopened and rendered |

Search the specified local EndNote library before online sources unless the user chooses otherwise. Add stage-specific fields to the manifest; preserve original wording, corrections, source attempts, file provenance, version, and unresolved states. Do not turn a missing PDF into a verified citation or a verified citation into a supported slide claim.

Keep Chinese-language publications, conference items, and website citations visible as user-handled items by default. Escalate title/DOI conflicts, edition mismatches, or inaccessible full text as explicit pending decisions. Report per-stage counts and links to deliverables, including missing items and limitations; the full workflow is complete only for stages actually requested and verified.
