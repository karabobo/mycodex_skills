---
name: medical-pptx-writing
description: Plan, research, write, design, and produce evidence-based medical PowerPoint decks with a causal storyline, traceable claims, and editable vector-first objects. Use for medical education, disease education, product training, clinical trial interpretation, mechanism, guideline, safety-management, competitive-landscape, or oncology decks, including creating a new deck, rebuilding a supplied deck, or turning a literature package into a presentation.
---

# Medical PPTX Writing

Create medical presentations as a controlled authoring workflow, not as one-shot slide generation.

This skill inherits the user's established style definition: **conclusion-driven, evidence-closed-loop, page-focused, and brand-restrained medical persuasion**. It is an authoring skill. Evidence verification is an internal control step supporting creation, not the audience-facing purpose of the deck.

The core sequence is:

`Brief -> evidence -> claim ledger -> causal storyline -> slide blueprint -> medical copy -> visual system -> editable PPTX -> render verification -> delivery`

## Required companion skills

- For local PPTX creation or editing, read and follow the installed `presentations` skill before implementation.
- For PDF rendering and visual verification, read and follow the installed `pdf` skill.
- If the user supplies a reference deck or template, preserve its master, layouts, typography, palette, and recurring components unless the user requests a redesign.

## Non-negotiable principles

1. Start from the clinical problem, not from product selling points.
2. Make each section answer a question created by the previous section.
3. Map every non-trivial medical claim to a source before finalizing copy.
4. Match population, analysis set, denominator, endpoint, cutoff, and statistical definition—not only the headline number.
5. Separate direct evidence, exploratory findings, mechanistic interpretation, and inference.
6. Use concise, presentation-ready Chinese or English; retain necessary medical qualifiers.
7. Build a native, editable PPTX. Do not flatten whole slides into images.
8. Use visual emphasis only to clarify evidence, never to exaggerate it.
9. Verify the final PPTX by rendering every slide and inspecting the visible result.
10. Keep internal review language out of audience-facing titles, key messages, and result boxes unless a short qualification is necessary to prevent material misunderstanding.
11. Use brand language mainly on covers, chapter dividers, and closing pages; keep evidence pages medically auditable and restrained.

## Layout and reference-list constraints (house rules)

These rules override generic PowerPoint advice whenever this skill produces, rebuilds, or repairs a deck.

- **Never add grouping locks.** Do not set `noGrp`（禁止组合）or "do not select"/lock flags on generated text boxes, vector shapes, connectors, icons, or groups. Every generated object must stay groupable and freely editable. Do not group or ungroup objects on your own initiative — grouping is the user's decision at edit time.
- **Typography defaults: 微软雅黑 (Microsoft YaHei) for Chinese, Arial for Latin text.** Emit both slots on every run (`<a:latin typeface="Arial"/>` and `<a:ea typeface="微软雅黑"/>`, with `<a:cs typeface="Arial"/>`), and set the same pair in the slide master/theme defaults so new objects inherit it. Do not leave the inherited theme font (usually Calibri/等线) in place, and do not mix in a third family for emphasis — use weight, size, or color instead.
- **The bottom-left reference list is one single text box per slide, set at 8 pt by default.** Never split it into several text boxes, one shape per reference, or an image. Set it in standard NLM short style matching `/Applications/EndNote 2025/Styles/nlm_short.ens`: authors, title, journal, year, volume(issue), pages or article number. Drop to 7 pt only when the reference list genuinely will not fit at 8 pt, never below 7 pt.
- **No DOI, URL, access date, or descriptive filler in that text box** — no `在线查看`, `查看原文`, `Available from:`, "accessed on", or similar. Identifiers belong in the evidence manifest, not the visible footnote.
- Keep the reference text box editable, and after rendering verify that it is complete, inside the slide, unclipped, and not overlapping other content.
- **No defensive hedging, no disclaimers, no extrapolation on slides.** Never write defensive or self-correcting wording (`不能证明`, `不能推出`, `不足以说明`, `不等于`, `并非`, `而不是`, `不是…而是…`, `尚不能`, `更准确地说`) and never write disclaimers (`仅供参考`, `仅供内部使用`, `尚需进一步验证`, "for reference only", "not medical advice"). State the result; do not argue with an absent objection. Do not widen a result past the population that was enrolled (`所有患者`, `全人群`, `class effect`). If the evidence cannot carry a sentence, cut the sentence instead of softening it.

## Workflow

### 1. Define the brief

Confirm or infer safely:

- disease, therapy, indication, treatment line, and geography;
- audience and use case;
- communication objective and desired audience takeaway;
- scope, approximate length, data cutoff, label version, and compliance boundary;
- available references, source package, brand deck, and template.

Do not begin slide writing until the communication job and medical boundary are clear.

### 2. Build the medical question framework

Organize the domain into the questions the audience must understand. Typical modules include disease burden, diagnosis/staging, treatment pathway, unmet need, mechanism, pivotal evidence, long-term follow-up, subgroups, safety, clinical application, guidelines, and competitive context.

For each module record:

- the clinical question;
- why it matters to this audience;
- the evidence type needed;
- the decision or understanding it should enable.

### 3. Build the evidence map and claim ledger

Prefer label/regulatory documents, original trials and supplements, updated analyses, guidelines, consensus statements, systematic reviews, then RWE. Do not force a nearby source to support a broader claim.

Create a claim ledger with at least:

`slide/topic | proposed claim | population/context | endpoint/data | source location | evidence status | wording limit`

Read [references/evidence-and-claims.md](references/evidence-and-claims.md) when sourcing, extracting, or validating medical claims.

### 4. Design the causal storyline

Write the deck's one-sentence causal chain before planning slides:

`clinical problem -> limitation of current practice -> therapeutic rationale -> clinical validation -> clinical meaning -> safe application`

Avoid parallel lists of benefits. Every chapter must contain:

1. **Clinical problem** — What remains unresolved?
2. **Medical answer** — Why might this approach address it?
3. **Clinical validation** — What evidence answers the question?
4. **Clinical meaning** — What changes for practice or understanding?
5. **Handoff question** — What must the next chapter answer?

Read [references/storyline-and-blueprint.md](references/storyline-and-blueprint.md) when creating or repairing narrative structure.

Select the dominant narrative mode before building chapters:

- **Guideline education:** guideline change -> why it changed -> treatment framework -> multidimensional evidence -> mechanism -> summary.
- **Value anchor:** establish the decisive clinical value -> expose the limitation of surrogate or prior strategies -> introduce the turning point -> validate across the disease course -> branded close.
- **Clinical evidence chain:** unmet need -> approval/guideline position -> rationale/mechanism -> pivotal evidence -> relevant population data -> safety -> application -> summary.

Read [references/authoring-style-dna.md](references/authoring-style-dna.md) for the established page grammar, title patterns, and brand/evidence balance.

### 5. Create the slide blueprint

Before designing, define each slide's job:

`slide purpose | question/conclusion title | key claim | evidence/visual | interpretation | clinical meaning | source | transition`

Rules:

- one primary communication task per slide;
- title, chart, interpretation, and takeaway must make the same claim;
- split overloaded slides instead of shrinking body text;
- remove slides that do not advance the narrative;
- use conclusion titles only when the evidence supports that strength.
- make the directory and final summary mirror each other; the summary must not introduce new evidence.
- write all slide titles first and read them consecutively; they should independently reproduce the argument.

### 6. Write presentation-ready medical copy

Use compact, natural, professional language. Preserve population, setting, endpoint, and qualification where required.

Avoid:

- translation-like syntax and long academic paragraphs;
- unsupported superlatives or causal language;
- calling exploratory subgroups “advantage populations” without interaction evidence;
- treating RWE as confirmation of an RCT;
- unmatched cross-trial comparisons;
- presenting changes across data cuts as patient-level risk continually falling.

Use wording such as `观察到`, `提示`, `可能为…提供机制基础`, `结果与…总体一致`, or `探索性分析` when appropriate.

Default content-page anatomy:

1. one audience-facing conclusion title;
2. one or two evidence modules;
3. exact key statistics and direct labels;
4. one sentence translating data into clinical meaning;
5. compact source, abbreviation, cutoff, or indispensable qualification.

Do not expose the claim ledger, evidence-status labels, wording downgrades, or reviewer comments on the main canvas. Store detailed boundaries in speaker notes, backup slides, or the internal source package unless omission would materially mislead.

### 7. Establish the visual system

Define slide size, safe margins, master/layout use, typography, theme colors, chart colors, title hierarchy, source treatment, image style, and recurring page types before beautifying individual slides.

Use hierarchy, alignment, whitespace, scale, and restrained color before decoration. Give each slide one visual center and a clear reading path.

### 8. Produce an editable, vector-first PPTX

Default object priority:

1. native PowerPoint text, shapes, connectors, tables, and charts;
2. SVG for scalable icons or scientific components;
3. raster only for photographs, radiology/pathology images, faithful source figures, or visuals that cannot be reliably reconstructed.

Keep titles, body copy, labels, data, legends, key numbers, citations, mechanism labels, and flowchart text editable. SVG scalability does not automatically mean component-level editability; convert or rebuild when future internal editing is expected.

Read [references/visual-and-editable-production.md](references/visual-and-editable-production.md) before layout, beautification, chart rebuilding, mechanism diagrams, or PPTX implementation.

### 9. Review medical meaning and visual integrity

Run separate passes for:

- evidence and medical accuracy;
- language, terminology, units, and consistency;
- promotional/compliance boundary;
- hierarchy, readability, and visual truthfulness;
- editability and master/layout consistency.

Do not let a visual redesign silently change a denominator, endpoint, scale, confidence interval, or statistical interpretation.

### 10. Render and verify

Render every final slide. Inspect slides individually at full size, not only as a montage.

Verify:

- no clipping, overlap, overflow, broken glyphs, or unexpected wrapping;
- charts, labels, axes, legends, risk tables, and footnotes are correct and readable;
- images are sharp and not distorted;
- repeated elements are consistent;
- key objects remain editable;
- the visible PDF matches the intended PPTX.

Read [references/delivery-and-qa.md](references/delivery-and-qa.md) before final delivery.

## Stage gates

Do not advance past a gate when a critical item is unresolved.

1. **Evidence gate:** every key claim has a source and evidence status.
2. **Storyline gate:** every section has a causal role and handoff.
3. **Blueprint gate:** every slide has one job and a defined source/visual.
4. **Medical gate:** copy does not exceed the evidence.
5. **Editability gate:** key content is not flattened.
6. **Visual gate:** latest render has no material defect or misleading emphasis, the bottom-left reference list is one intact text box in NLM short style, and generated objects carry no grouping locks.

## Deliverables

Depending on scope, deliver:

- final editable PPTX;
- final PDF;
- source package or source manifest;
- evidence map and claim ledger;
- slide blueprint or storyline map;
- review/change log;
- data cutoff and version identifier.

Report any intentionally rasterized components and any remaining evidence or editability limitations.

## Reusable prompt sequence

Use these prompts in order when the user asks for end-to-end authoring:

1. **Brief:** define audience, occasion, duration, medical objective, desired audience change, evidence boundary, template, brand, and data cutoff.
2. **Evidence map:** extract population, intervention, comparator, endpoint, result, analysis set, cutoff, source location, and wording limit.
3. **Storyline:** choose a dominant narrative mode and build a causal chapter chain with explicit handoffs.
4. **Blueprint:** assign each slide one purpose, one conclusion title, evidence, clinical meaning, transition, and source.
5. **Copy:** write concise audience-facing medical copy without internal review language.
6. **Visual/editable production:** apply a coherent visual system and build native/vector-first PowerPoint objects.
7. **Render QA:** inspect every rendered slide at full size and correct both visible and structural defects.
