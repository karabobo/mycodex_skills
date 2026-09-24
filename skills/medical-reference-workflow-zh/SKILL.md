---
name: medical-reference-workflow-zh
description: 用中文统筹医学 PPT 参考文献全流程：引文提取、DOI 题录核实、优先查本地 EndNote、联网获取 PDF、按需科研通求助及论断高亮。
---

# 医学参考文献组合流程

仅执行用户要求的阶段。“收集 PDF”本身不代表授权核验所有医学论断、发布文献求助或采纳他人上传文件。

当两个及以上阶段共用清单时，修改前先读 [references/handoff-contract.md](references/handoff-contract.md)。该契约区分一篇文献、每次 PPT 引用和每条论断，不要求为此重建用户现有表格。

| 阶段 | Skill | 交接标准 |
| --- | --- | --- |
| PPT 引文提取 | `pptx-citation-inventory-zh` | 全部渲染页已核对，原始写法及重复出现页码保留 |
| DOI 与题录核实 | `bibliographic-metadata-resolver-zh` | 每篇作品有已核实身份或明确的未解决原因 |
| 本地 EndNote 检索 | `endnote-pdf-retrieval-zh` | 指定库只读检索，复制件哈希核对 |
| 联网来源查找 | `literature-source-archive-zh` | 未解决文献逐来源核查，PDF 归档注明来源与版本 |
| 英文科研通求助，按需 | `ablesci-literature-assist-zh` | 每次一篇 DOI，核对题录及文件后再决定是否采纳 |
| 全套页面论断审计，按需 | `pdf-claim-highlighter-zh` | 范围内每项论断有判断及证据位置 |
| 逐篇精选文献高亮，按需 | `selective-literature-highlight-zh` | 仅标注获支持的短片段，副本已重新打开并渲染检查 |

除非用户指定其他顺序，先查指定 EndNote 库，再查联网来源。持续扩展清单的阶段字段，保留原文、纠正信息、检索尝试、PDF 来源和版本、未解决状态。“缺 PDF”“有 PDF”“论断有证据”是三种不同状态，不得混同。

中文文献、会议项目与网址引用默认保留为用户自行处理项。标题/DOI 冲突、版本不符、全文不可及要明确列为待处理。最终按实际执行阶段汇总数量、交付物和限制；未执行的阶段不得报告为完成。
