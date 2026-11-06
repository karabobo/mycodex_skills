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

## Medical-boundary statements

### Membership test

A sentence is a boundary statement when it answers at least one of four questions about a claim:

1. **Applicability** — who the result may be used for: population, subgroup, line, stage, setting, geography, indication.
2. **Conditions** — under which design conditions it holds: regimen, combination, follow-up, data cutoff, analysis set.
3. **Limits** — where it does not hold: not studied, exploratory, post hoc, indirect comparison, off-label.
4. **Compliance boilerplate** — `仅供参考`, `仅供内部使用`, "not medical advice", "internal training only". These count as boundary text, and the rule deletes them.

Run these three questions in order; the first "yes" makes it a boundary statement:

- Delete the sentence in your head: does the reader's answer to *"who may this number be used for?"* change? If yes, it is a boundary statement.
- Does it carry an applicability marker — 适用 / 仅限 / 不用于 / 所有 / 均可 / 同样 / 尚未 / 未证实 / 探索性 / 事后分析 / 亚组 / 一线 / 超说明书, or *in, only, not indicated, all patients, similar, exploratory, post hoc, subgroup, line, off-label*? If yes, it is a boundary statement.
- Does it go beyond restating the result by adding a scope or a condition? If yes, it is a boundary statement.

Not boundary statements — leave them alone and keep them out of this rule:

- the result sentence itself: `In DESTINY-Breast04, PFS HR 0.51 (95% CI 0.40–0.64)`;
- design and methods sentences;
- background epidemiology and unmet-need framing;
- mechanism explanation;
- reference footnotes and citation text.

### What the statement may contain

A boundary statement is allowed to carry exactly three elements:

| Element | What must match the source |
|---|---|
| Population | The enrolled population and analysis set, not the intended or eligible one; subgroup only if it was pre-specified and analysed. Evidence-strength labels that belong to the analysis (exploratory, post hoc, pre-specified) stay attached here instead of becoming a separate caveat sentence |
| Data | The reported value with its unit and endpoint definition, at the same time point, over the same denominator |
| 95% CI | Both bounds, the same interval type, the same direction of effect, and the same rounding |

Verify element by element against the exact source location before the claim is
written; a mismatch in any one of them means the statement is rewritten from the
source, not paraphrased.

Everything else is deleted rather than softened:

- extrapolation to populations, lines, or settings outside the enrolled one;
- mechanism, rationale, or "therefore" commentary that turns a result into a recommendation;
- comparative framing and `first`, `only`, `preferred`, `best-in-class` claims;
- template disclaimers such as `仅供参考`, `仅供内部使用`, `本材料不构成医疗建议`, or "for internal training only";
- hedging that keeps an over-broad claim while adding a caveat — cut the overreach, not the number.

If a compliant deliverable genuinely needs a disclaimer or a data cutoff line,
that is a separate, user-supplied string placed where the user asks, not a
substitute for the three-element boundary statement and not something this skill
invents on its own.

### Worked examples

| Original wording | Verdict | Rendered |
|---|---|---|
| `该药可用于所有 HER2 低表达患者` | boundary — extrapolates beyond enrolment | `DESTINY-Breast04 入组 HER2 低表达、既往化疗后患者：PFS HR 0.51（95% CI 0.40–0.64）` |
| `ORR 58%（95% CI 45–70），该结果来自探索性亚组` | boundary — applicability plus a detached caveat | `探索性亚组（n=41）：ORR 58%（95% CI 45–70）` — the label moves onto the population element |
| `PFS HR 0.51（95% CI 0.40–0.64）` | result sentence, not a boundary statement | unchanged |
| `仅供参考，不构成医疗建议` | compliance boilerplate | deleted unless the user asks for it as a separate fixed string |
| `亚组结果提示该方案可能更优，尚需进一步验证` | boundary — comparative claim plus hedging | deleted; keep only the pre-specified subgroup population, value, and CI, or drop the claim |

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

## Evidence prompt

> Build an evidence map for the listed medical questions. Prefer labels, original trials, supplements, updated follow-up, and authoritative guidelines. For every result, record population, analysis set, denominator, endpoint definition, cutoff, follow-up, statistic, source location, and limitations. Separate direct evidence, exploratory findings, mechanistic rationale, and inference. Mark missing fields as unverified; do not force a nearby source to support a broader claim.

## Claim verification prompt

> Evaluate whether this proposed slide claim is directly supported by the cited source. Check population, treatment line, analysis set, denominator, endpoint, cutoff, follow-up, statistic, and wording strength. Identify correlation-to-causation, subgroup overreach, cross-trial comparison, or mechanism-to-outcome overreach. Return evidence status, exact supporting location, risk, and a presentation-ready revision.

