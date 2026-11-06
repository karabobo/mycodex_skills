# Multi-Agent Skills Archive

This repository stores canonical skills once and renders agent-specific variants
for Codex, DeepSeek Harness, Cline, Cursor, Gemini CLI, pi, and future agents.
It follows the bigpowers model: **edit `skills/` only; generated adapter output is
never hand-edited**.

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
skills/                        # canonical source (Codex-flavoured)
  excel-forest-plot/
  ablesci-literature-assist/
  ablesci-literature-assist-zh/
  pptx-citation-inventory-{en,zh}/
  bibliographic-metadata-resolver-{en,zh}/
  endnote-pdf-retrieval-{en,zh}/
  literature-source-archive-{en,zh}/
  pdf-claim-highlighter-{en,zh}/
  selective-literature-highlight-{en,zh}/
  medical-reference-workflow-{en,zh}/
scripts/
  sync_from_codex_skills.sh    # pull new skills from ~/.codex/skills
  sync-skills.sh               # render + validate + index for DSH
  sync_skills.py               # the renderer driver
  validate_dsh_skills.py       # DSH contract linter
  generate_skill_index.py      # writes SKILL-INDEX.md
  lib/skill_ir.py              # Parse -> IR (platform-neutral record)
  adapters/dsh.py              # IR -> DSH skill tree
tests/
  test_dsh_adapter.py
.dsh/skills/                   # GENERATED — the DSH rendering (gitignored)
SKILL-INDEX.md                 # GENERATED — navigation index (gitignored)
skills-to-archive.txt
```

The medical-reference workflow has separate English and Chinese entry points.
It resolves DOI and bibliographic metadata after citation extraction, then
checks the named local EndNote library before online sources. AbleSci is an
optional, separately authorized stage for English-language literature only.
For multi-stage runs, each workflow entry point includes a handoff contract that
keeps publications, slide citations, and individual claims distinct without
requiring the user's existing spreadsheet to be rebuilt.

## Multi-Agent Rendering

Target definitions live in `config/targets.json`. The single driver reads that
file and dispatches each canonical `SkillIR` record to the named adapter.
Generated output directories are ignored by Git and should not be edited.

```bash
./scripts/sync-skills.sh --target dsh
./scripts/sync-skills.sh --target codex
python3 scripts/sync_skills.py --target all
python3 scripts/sync_skills.py --target cursor --output /tmp/mycodex-cursor
```

Initial targets are DSH, Codex, Cline, Cursor, Gemini CLI, and pi. Adding a
new agent means adding its output contract to `config/targets.json`, writing an
adapter under `scripts/adapters/`, registering it, and adding renderer tests;
the canonical skill bodies remain unchanged.

## Sync From Local Codex Skills

Edit `skills-to-archive.txt` and add one skill folder name per line.

Then run:

```bash
./scripts/sync_from_codex_skills.sh
```

The script copies listed skills from `${CODEX_HOME:-$HOME/.codex}/skills` into `skills/`.

## Rendering for DeepSeek Harness

DSH discovers a skill at `<root>/<name>/SKILL.md` (a directory bundle) or
`<root>/<name>.md` (flat). Nested `**/SKILL.md` is **not** discovered. Its
frontmatter contract differs from Codex in four ways that matter:

| Concern | Codex | DeepSeek Harness | What the adapter does |
| --- | --- | --- | --- |
| Frontmatter keys | accepts `disableModelInvocation`, `modelInvocable`, `userInvocable` | **rejects** them (throws) | drops them, emits kebab-case `disable-model-invocation` / `user-invocable` |
| Description length | unbounded | catalog truncates at 500 normalized chars | rebalances so the scope clause survives |
| Trigger hint | `whenToUse` unused | `whenToUse` rendered in the catalog | carried through |
| Codex artifacts | `agents/openai.yaml` used | ignored | not copied |

The description case is the one that bites. `ablesci-literature-assist`'s
description is 527 characters, so DSH's own truncation would cut it at
`...Do not use this skill for Chinese-language or...` — losing exactly the
clause that tells the model when *not* to use the skill. The adapter instead
trims the positive clause and always keeps the negative scope clause whole.

### Usage

```bash
./scripts/sync-skills.sh              # render .dsh/skills, validate, reindex
./scripts/sync-skills.sh --install    # also install into ~/.dsh/skills
./scripts/sync-skills.sh --check      # validate only, render nothing
```

Install roots, in the order DSH resolves duplicates (lower rank wins):

| Rank | Root | Scope |
| --- | --- | --- |
| 100 | `<project>/.dsh/skills` | this project |
| 200 | `<project>/.agents/skills` | this project (agents convention) |
| 300 | `Config.customSkillDirs` | custom directories |
| 400 | `~/.dsh/skills` | this user |
| 500 | `~/.agents/skills` | this user (agents convention) |
| 600 | bundled | shipped with DSH |

`--install` writes to `~/.dsh/skills` (rank 400) unless `--install-root`
overrides it. To scope the install to a single project instead, point it at
`<project>/.dsh/skills` (rank 100) — that wins over the user-level copy.

### Validation

`scripts/validate_dsh_skills.py` encodes the DSH loading rules and fails on
anything that would silently break a skill:

| Rule | Check |
| --- | --- |
| R1 | no nested `SKILL.md` (DSH does not discover it) |
| R2 | `name` matches `^[a-z0-9]+(?:-[a-z0-9]+)*$` and equals the directory name |
| R3 | `name` and `description` present |
| R4 | `description` ≤ 500 normalized characters |
| R5 | no legacy frontmatter keys |
| R6 | invocation-policy fields are booleans |
| R7 | relative paths referenced in the body resolve inside the skill |
| R8 | no leftover `agents/openai.yaml` (warning) |

### Tests

```bash
cd mycodex_skills && python3 -m unittest discover -s tests -v
```

Run from the repository root — `unittest discover` refuses a relative start
directory otherwise. Requires Python 3.9+ (no third-party dependencies).

### Architecture

The pipeline follows the bigpowers pattern: **Parse → IR → Render**.

- `scripts/lib/skill_ir.py` parses each `SKILL.md` into a `SkillIR` record —
  a platform-neutral dataclass. Frontmatter parsing is a minimal flat-YAML
  reader so the repo needs no dependencies.
- `scripts/adapters/` contains one renderer per agent target. `dsh.py` applies DeepSeek Harness rules; `codex.py` materializes a Codex-target tree. `registry.py` selects a named adapter, so each target is adapted once and future syncs regenerate it instead of repeatedly editing skill bodies.
- Select a target explicitly: `./scripts/sync-skills.sh --target dsh` or `./scripts/sync-skills.sh --target codex --output .agents/codex/skills`. Adding a new agent means adding one adapter module and registering it; the canonical skills and parser remain unchanged.

## Privacy

This repository is public. Keep client names, local paths, credentials, and
unpublished work products out of it. Use a separate private repository for
skills that contain work-specific procedures or internal templates.
