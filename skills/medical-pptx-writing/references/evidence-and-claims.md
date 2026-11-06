# Evidence and Claim Control

## Source priority

1. Current label and regulatory documents
2. Original pivotal publication and supplement/appendix
3. Updated follow-up publication or conference abstract
4. Current authoritative guideline
5. Consensus statement
6. Systematic review or meta-analysis
7. Real-world evidence
8. Secondary interpretation

Do not treat an appendix as a separate trial. Keep different cutoffs and analysis sets distinct.

## Data extraction fields

For each study extract:

- citation and study name;
- phase and design;
- population, line, geography, and eligibility;
- randomized and analyzed sample sizes;
- treatment, dose, schedule, and duration;
- primary, secondary, and exploratory endpoints;
- result, unit, HR/OR/RR, 95% CI, and P value;
- analysis set, denominator, cutoff, and follow-up;
- safety definition and exposure window;
- exact source page, table, figure, or appendix location;
- limitations.

Use `尚未确认` instead of inference when a field cannot be verified.

## Claim ledger schema

| Field | Requirement |
|---|---|
| Slide/topic | Stable locator |
| Proposed claim | Exact audience-facing wording |
| Population/context | Indication, line, subgroup, geography |
| Endpoint/data | Full statistic and definition |
| Source | Exact paper, label, guideline, or appendix |
| Source location | Page/table/figure/section |
| Evidence status | Direct / qualified / exploratory / mechanistic / unsupported / unchecked |
| Wording limit | Required qualifier or prohibited interpretation |

## Evidence status language

- **Direct:** source explicitly supports the claim.
- **Qualified:** core claim is supported only with population, cutoff, or endpoint qualification.
- **Exploratory:** subgroup, post hoc, biomarker, or hypothesis-generating analysis.
- **Mechanistic:** biologically plausible rationale without direct clinical causal proof.
- **Unsupported:** cited source does not support the wording.
- **Unchecked:** not yet verified against the original source.

## Hard boundaries

- Do not turn association into causality.
- Do not call an exploratory subgroup a preferred population without appropriate interaction evidence.
- Do not call retrospective or single-arm RWE proof of RCT efficacy.
- Do not directly rank therapies using unmatched cross-trial values.
- Do not mix global and regional data, confirmed and unconfirmed response, or different safety definitions.
- Do not interpret changing HR point estimates across follow-up cuts as a patient's risk continually decreasing.
- Do not use mechanistic engineering features as proof of superior clinical efficacy or safety.

## Forbidden slide wording

No defensive hedging or self-correcting wording on a slide.

- Defensive wording: 不能推出、不能证明、不能仅凭、只能证明、不能据以、不足以说明、不能简单说、不能解释、不能断言、不能认定、不能确定、不能确认、不能保证、不能承诺、不能断定、不能当作、不能当做、不能视为、不能直接、不能只看、无法说明、无法证明、不等于、不等同于、并非、并不是、而不是、不是…而是…、不代表、不构成、未必、尚不能、还不能、更准确地说.
- Disclaimers: 仅供参考、仅供内部使用、本材料不构成医疗建议、请咨询专业医师、尚需进一步验证、有待证实、初步结果显示、可能有效；for reference only, not medical advice, further validation is needed.
- Extrapolation: 所有患者、全人群、同类药物均可、class effect、真实世界同样有效、可推广至…

A slide answers two things only: what the result was (statistic, 95% CI, source page) and who it belongs to (the population actually enrolled).

## Evidence prompt

> Build an evidence map for the listed medical questions. Prefer labels, original trials, supplements, updated follow-up, and authoritative guidelines. For every result, record population, analysis set, denominator, endpoint definition, cutoff, follow-up, statistic, source location, and limitations. Separate direct evidence, exploratory findings, mechanistic rationale, and inference. Mark missing fields as unverified; do not force a nearby source to support a broader claim.

## Claim verification prompt

> Evaluate whether this proposed slide claim is directly supported by the cited source. Check population, treatment line, analysis set, denominator, endpoint, cutoff, follow-up, statistic, and wording strength. Identify correlation-to-causation, subgroup overreach, cross-trial comparison, or mechanism-to-outcome overreach. Return evidence status, exact supporting location, risk, and a presentation-ready revision.

