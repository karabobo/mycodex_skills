# Visual and Editable PPTX Production

## Visual system first

Define before slide production:

- slide size and safe margins;
- source deck master and layouts;
- title, subtitle, body, label, and citation hierarchy;
- theme and functional colors;
- chart palette and treatment-arm consistency;
- image, icon, mechanism, and table style;
- recurring page archetypes.

Use one visual center per slide. Establish reading order through position, scale, whitespace, alignment, and restrained color. Split content before shrinking text.

## Editable object priority

1. Native PowerPoint text, shapes, connectors, tables, and charts
2. SVG for scalable icons and scientific components
3. Raster only for photographs, scans, pathology/radiology, faithful source figures, or visuals that cannot be reliably reconstructed

Never flatten a whole slide merely to preserve appearance.

Keep these editable:

- titles and body copy;
- key numbers, labels, legends, and annotations;
- tables and chart data where practical;
- flowchart and mechanism labels;
- references and footnotes;
- brand colors and repeated components.

SVG is scalable but may still be a single object. If future component-level editing is expected, rebuild or convert it into native shapes. Keep external SVG/data source files with the deliverable when relevant.

## Charts

Prefer native charts or editable vector reconstruction. Preserve:

- exact data and analysis set;
- axis meaning and scale;
- units and endpoint names;
- HR/CI/P value;
- risk tables and censoring information when material;
- cutoff and source.

Do not crop or recolor a source figure in a way that changes interpretation. If a faithful source image must remain raster, place interpretation in editable native text beside it.

## Mechanism diagrams

Build with independent scientific components, connectors, and editable labels when possible. Create connectors before nodes so they remain behind entities. Keep mechanism, evidence, and clinical outcome visually distinct. Do not depict an unproven causal bridge as established.

## Tables

Use native tables or shapes, not screenshots. Keep headers, units, denominators, footnotes, and values editable. Split dense tables instead of reducing them to unreadable sizes.

## Beautification prompt

> Beautify this medical slide without changing medical meaning. Preserve all validated data and qualifiers. Improve hierarchy, alignment, spacing, reading order, typography, and restrained brand-color use. Delete repetition or split the slide before shrinking text. Keep all new text, shapes, labels, and icons editable. Do not flatten the slide, alter statistics, hide confidence intervals, or use visual emphasis that exceeds the evidence.

## Editable production prompt

> Produce a native, vector-first, editable PPTX. Use native text, shapes, connectors, tables, and charts wherever practical; SVG for scalable scientific/icon components; and raster only for photographs, medical images, or source figures that cannot be reliably rebuilt. Do not flatten whole slides. Keep key data, labels, legends, citations, and mechanism text editable. Report which components are native, SVG, raster, or only partially editable and why.

## Editability levels

- **Fully editable:** native text, shapes, tables, charts, and connectors.
- **Vector editable:** scalable vector object, with limited internal editing unless converted.
- **Partially editable:** native copy around unavoidable raster source content.
- **Flattened:** whole slide or key content is a single image; unacceptable unless explicitly requested.

Target fully editable delivery; allow partially editable content only with a stated scientific or technical reason.


## Grouping locks: never add them

A shape is made ungroupable in OOXML by `<a:spLocks noGrp="1"/>` inside `<p:cNvSpPr>`; a group can be locked through attributes on `<p:cNvGrpSpPr>`. Both are "禁止组合" markers. Do not emit them on anything you generate, and clear them when a supplied template or a round-trip through another converter introduced them.

- With python-pptx, `shapes.add_textbox` / `add_shape` do not set these locks; the risk comes from copying template shapes, copying XML from a source deck, or exporting/reimporting through LibreOffice.
- Check before delivery (expect 0 for generated slides):

```bash
unzip -p deck.pptx 'ppt/slides/slide*.xml' | grep -o 'noGrp="1"' | wc -l
```

- Leave grouping state alone: do not group, ungroup, or "merge into one object" unless the user asks. Independent objects stay independently editable.

## Font defaults

- Chinese text: `微软雅黑` (Microsoft YaHei). Latin text: `Arial`.
- In OOXML, write both slots on every run and on the master defaults:

  ```xml
  <a:rPr ...><a:latin typeface="Arial"/><a:ea typeface="微软雅黑"/><a:cs typeface="Arial"/></a:rPr>
  ```

- Set the pair once in `ppt/theme/theme1.xml` (`<a:majorFont>`/`<a:minorFont>`) so shapes created later inherit it; per-run overrides are then only needed for exceptions.
- A deck that inherits Calibri or 等线 because the theme was never touched is a defect: it renders differently on machines without those fonts and breaks the intended look. Spot-check with `unzip -p deck.pptx ppt/theme/theme1.xml | grep -o 'typeface="[^"]*"' | sort -u`.
- Do not introduce a third family for emphasis or headings; differentiate with size, weight, and color.
- Title size: 24 pt by default, 20–32 pt allowed. Anything below 20 pt is a defect — shorten the title or split the slide instead. Everything else (body, meaning line, labels) sits below the title and never goes above 32 pt.
- Fonts are named, not embedded by default. If the deliverable must look identical on a machine without 微软雅黑/Arial, say so rather than silently substituting.

## Bottom-left reference list

- Build exactly one text box per slide, anchored bottom-left, spanning the content width above the bottom margin, aligned with the left text margin.
- One paragraph per reference in NLM short style (`nlm_short.ens`): authors, title, journal, year, volume(issue), pages or article number. Apply NLM author truncation (first six authors then "et al.") as the style does.
- Type size 8 pt by default; tighten line spacing rather than dropping size. Go to 7 pt only when the list genuinely cannot fit, and never below 7 pt. No bullets, no images, no per-reference shapes.
- Never include DOI, URL, access date, or descriptive filler such as `在线查看`, `查看原文`, `Available from:`, or "accessed on". Keep those in the evidence manifest.
- After the render pass, confirm the box is complete, unclipped, inside the slide, and not covered by other objects.
