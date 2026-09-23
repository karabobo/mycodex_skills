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
  endnote-pdf-retrieval-{en,zh}/
  literature-source-archive-{en,zh}/
  pdf-claim-highlighter-{en,zh}/
  medical-reference-workflow-{en,zh}/
scripts/
  sync_from_codex_skills.sh
skills-to-archive.txt
```

The medical-reference workflow has separate English and Chinese entry points.
It checks the named local EndNote library before online sources. AbleSci is an
optional, separately authorized stage for English-language literature only.

## Sync From Local Codex Skills

Edit `skills-to-archive.txt` and add one skill folder name per line.

Then run:

```bash
./scripts/sync_from_codex_skills.sh
```

The script copies listed skills from `${CODEX_HOME:-$HOME/.codex}/skills` into `skills/`.

## GitHub Setup

Create a private GitHub repository, then connect this local archive:

```bash
git remote add origin git@github.com:<github-user>/<repo-name>.git
git branch -M main
git push -u origin main
```

Use a private repository when skills contain work-specific procedures, client names, internal templates, or unpublished workflows.
