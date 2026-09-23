# Codex Skills Archive

This repository archives personal Codex skills for version history, backup, and GitHub synchronization.

## Policy

Archive only personal skills that were created or customized intentionally.

Do not archive:

- `.system` skills
- plugin cache folders
- generated runtime state
- credentials, tokens, browser profiles, or service account files
- large generated outputs unless they are deliberate templates or examples

## Structure

```text
skills/
  excel-forest-plot/
  ablesci-literature-assist/
  ablesci-literature-assist-zh/
  pptx-citation-inventory-{en,zh}/
  bibliographic-metadata-resolver-{en,zh}/
  endnote-pdf-retrieval-{en,zh}/
  literature-source-archive-{en,zh}/
  pdf-claim-highlighter-{en,zh}/
  medical-reference-workflow-{en,zh}/
scripts/
  sync_from_codex_skills.sh
skills-to-archive.txt
```

The medical-reference workflow has separate English and Chinese entry points.
It resolves DOI and bibliographic metadata after citation extraction, then
checks the named local EndNote library before online sources. AbleSci is an
optional, separately authorized stage for English-language literature only.
For multi-stage runs, each workflow entry point includes a handoff contract that
keeps publications, slide citations, and individual claims distinct without
requiring the user's existing spreadsheet to be rebuilt.

## Sync From Local Codex Skills

Edit `skills-to-archive.txt` and add one skill folder name per line.

Then run:

```bash
./scripts/sync_from_codex_skills.sh
```

The script copies listed skills from `${CODEX_HOME:-$HOME/.codex}/skills` into `skills/`.

## Privacy

This repository is public. Keep client names, local paths, credentials, and
unpublished work products out of it. Use a separate private repository for
skills that contain work-specific procedures or internal templates.
