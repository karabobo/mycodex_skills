---
name: medical-reference-workflow-en
description: "Coordinate a medical slide literature workflow: PPTX citation extraction, prioritized local EndNote lookup, online source retrieval, optional English AbleSci requests, and claim-level PDF verification/highlighting."
---

# Medical reference workflow

Use this when the user asks for the whole chain. Invoke the component skills only for requested stages; a request to collect PDFs does not itself authorize claim-level review, posting a mutual-aid request, or accepting a submitted file.

| Stage | Skill | Handoff condition |
| --- | --- | --- |
| Slide citation inventory | `pptx-citation-inventory-en` | Every rendered slide checked; raw citations and repeat occurrences retained |
| Local EndNote lookup | `endnote-pdf-retrieval-en` | Named library searched read-only; copied files hash-verified |
| Online source acquisition | `literature-source-archive-en` | Unresolved works checked across lawful sources; each attempt and verified PDF attributed |
| English mutual aid, when requested | `ablesci-literature-assist` | One DOI at a time; metadata and downloaded file verified before acceptance |
| Claim audit and highlights, when requested | `pdf-claim-highlighter-en` | Every in-scope claim has a verdict and source location; highlighted copies reopened |

Use one stable citation/work ID across stages and keep slide occurrences separate. Search the specified local EndNote library before online sources unless the user chooses otherwise. Add stage-specific fields to the same manifest; preserve original wording, corrections, source attempts, file provenance, version, and unresolved states. Do not turn a missing PDF into a verified citation or a verified citation into a supported slide claim.

Keep Chinese-language publications, conference items, and website citations visible as user-handled items by default. Escalate title/DOI conflicts, edition mismatches, or inaccessible full text as explicit pending decisions. Report per-stage counts and links to deliverables, including missing items and limitations; the full workflow is complete only for stages actually requested and verified.
