---
name: selective-literature-highlight-zh
description: 对医学论断所引文献制作关键、简洁、克制、可见的原生 PDF 精选高亮；适用于逐篇核对后的证据标记，不用于装饰性大片涂色或整套 PPT 论断审计。
---

# 文献精选核对高亮

输入：页面实际表述、引文/文献 ID、候选原文 PDF。输出：保持不变的原件、仅在证据核实后另存的高亮副本，以及每条论断一行的核对台账。整套 PPT 的逐条论断审计交给 `pdf-claim-highlighter-zh`；本 skill 专注文献级的精选标注。

先读[共享证据与验收规则](../medical-reference-workflow-zh/references/evidence-review.md)，沿用用户授权的 `highlight_mode` 与 `annotation_policy`。

1. **先核对。** 比对 PDF 可见题名、首作者、年份、DOI 及正文/补充材料版本。定位与该命题对应的结果句、定义、表格单元格、图或限定脚注；阅读方法和上下文，区分本研究结果与引言转述；记录 PDF 页码、不同的印刷页码和简短摘录。文献身份或证据关系不清时，只记原因，不高亮。
2. **关键。** 选让读者足以复核论断的最短证据片段：通常是一句结果或相关表格单元格，并包括改变解释的限定语。孤立数字若缺人群、分母、终点或时间点，不算完整证据。
3. **简洁、克制。** 每条论断只做少量短句级、可编辑的原生 PDF Highlight。避免整段、整表、重复涂抹和遮字的不透明色块；不要造成“整篇论文或整条建议都获背书”的印象。原件保持未标注。扫描页先目视确认文字，再按坐标标记。
4. **可见。** 使用清楚但低遮挡的颜色和透明度；柔和金色、约 0.3 透明度可作起点，用户给了样例则先参照样例。保存后重新打开并渲染，每个标注页都按正常阅读大小检查：位置准确、正文和表格线可读、页数不变，副本能在常见 PDF 阅读器打开。
5. 台账记录 `claim_id`、原话、文献 ID、源文件/版本及哈希、PDF/印刷页、摘录/位置、判断、高亮数量、副本路径与限制说明。批量成包时保留原始引文编号和顺序，并用台账与实际文件数核对。

判断区分 `supported`、`partially_supported`、`contradicted`、`not_found`、`source_mismatch`。默认 `direct_support` 标获支持的最小命题；`closest_passage` 需用户授权，可标相关观察与限制，但不升级原句判定。所有差异外置。用户要求无文字批注时按 `color_only` 输出。优先运行 [scripts/check_pdf_highlights.mjs](scripts/check_pdf_highlights.mjs)（纯 JavaScript，不依赖 PyMuPDF）；若当前环境明确可导入 `fitz`，再运行 [scripts/check_pdf_highlights.py](scripts/check_pdf_highlights.py) 作为额外交叉检查。技术检查不替代语义和视觉验收。高亮只说明“这处原文与论断直接相关”，不等于更广泛的临床建议或证据等级已获证实。

整理 PPTX 文献包的 PDF 命名遵循 [交接契约中的命名规则](../medical-reference-workflow-zh/references/handoff-contract.md#pptx-文献包-pdf-命名)；沿用全部页码与页内序号，原件和高亮副本分目录保存，文件名不添加 `highlight` 或 `highlighted`。
