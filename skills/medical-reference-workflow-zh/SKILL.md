---
name: medical-reference-workflow-zh
description: 用中文统筹医学 PPT 参考文献全流程：引文提取、DOI 题录核实、优先查本地 EndNote、联网获取 PDF、按需科研通求助及论断高亮。
---

# 医学参考文献组合流程

仅执行用户要求的阶段。“收集 PDF”本身不代表授权核验所有医学论断、发布文献求助或采纳他人上传文件。

## PPTX 版式与参考文献约束

这些是用户既定约束，生成或修复幻灯片时始终生效；需要撰写整份 PPT 时交给 `medical-pptx-writing`。

- 自定义生成的文本框、矢量形状、连接线、图标及其他形状**不要添加「禁止组合」**（`noGrp`）、锁定或「不可选择」标记；对象应保持可组合、可编辑。也不要擅自执行组合/取消组合，分组由用户在编辑时决定。
- 每页左下角的参考文献列表必须是**一个完整的文本框**，不要拆成多个文本框、逐条独立形状或图片。文本框内使用标准 NLM short 格式，样式参考本机 `/Applications/EndNote 2025/Styles/nlm_short.ens`；作者、题名、期刊、年份、卷期、页码/文章号等必要字段按该样式输出。
- 参考文献文本框中**不得出现 DOI、URL、访问日期，也不得出现 `在线查看`、`查看原文`、`Available from:` 之类的描述性文字**；这些标识放清单，不放页脚。
- 参考文献文本框应保持可编辑，并在渲染后检查左下角是否完整显示、无溢出或遮挡。交付前可用 `unzip -p <deck.pptx> 'ppt/slides/slide*.xml' | grep -c 'noGrp="1"'` 抽查是否误加了禁止组合。

整理 PPTX 文献包（含 PDF 命名）或两个及以上阶段共用清单时，修改前先读 [references/handoff-contract.md](references/handoff-contract.md)。该契约区分一篇文献、每次 PPT 引用和每条论断，不要求为此重建用户现有表格。

涉及论断核对或高亮时，再读 [references/evidence-review.md](references/evidence-review.md)，向子阶段传递 `highlight_mode`、核对范围及 `annotation_policy`，不重置用户选择。先验证指定路径和既有可用解释器；环境故障只做有限定位并及时报告，不记作文献不存在。

| 阶段 | Skill | 交接标准 |
| --- | --- | --- |
| PPT 引文提取 | `pptx-citation-inventory-zh` | 全部渲染页已核对，原始写法及重复出现页码保留 |
| DOI 与题录核实 | `bibliographic-metadata-resolver-zh` | 每篇作品有已核实身份或明确的未解决原因 |
| 本地 EndNote 检索 | `endnote-pdf-retrieval-zh` | 指定库只读检索，复制件哈希核对 |
| 联网来源查找 | `literature-source-archive-zh` | EndNote 未命中后按「开放获取 → 用户已授权机构访问 → 用户授权 Sci-Hub 兜底」顺序尝试；逐来源核查，PDF 归档注明来源与版本 |
| 英文科研通求助，按需 | `ablesci-literature-assist-zh` | 每次一篇 DOI，核对题录及文件后再决定是否采纳 |
| 全套页面论断审计，按需 | `pdf-claim-highlighter-zh` | 范围内每项论断有判断及证据位置 |
| 逐篇精选文献高亮，按需 | `selective-literature-highlight-zh` | 按已授权模式标短片段，证据判定不变；语义与位置分别验收 |

除非用户指定其他顺序，先查指定 EndNote 库，再查联网来源；联网来源内部先走开放获取与用户已授权机构访问，仍未命中才使用用户授权的 Sci-Hub 兜底（`literature-source-archive-zh/scripts/scihub_fetch.mjs`）。持续扩展清单的阶段字段，保留原文、纠正信息、检索尝试、PDF 来源和版本、未解决状态。“缺 PDF”“有 PDF”“论断有证据”是三种不同状态，不得混同。

中文文献、会议项目与网址引用默认保留为用户自行处理项；用户已提供或另行授权时继续相应阶段。首次交付须逐项覆盖已授权范围，允许明确例外，不以文件/高亮总数代替论断覆盖；增量修订记录基线、合并状态和当前入口。标题/DOI 冲突、版本不符、全文不可及要明确列为待处理。最终按实际执行阶段汇总数量、交付物和限制；未执行的阶段不得报告为完成。
