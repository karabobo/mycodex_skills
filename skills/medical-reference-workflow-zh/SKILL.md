---
name: medical-reference-workflow-zh
description: 统筹医学 PPT 参考文献全流程：逐页提取引文、核实 DOI 和题录、优先查本地 EndNote、联网查找 PDF、按需科研通求助，以及原文核对与高亮。
---

# 医学参考文献组合流程

仅执行用户要求的阶段。“收集 PDF”本身不代表授权核验所有医学论断、发布文献求助或采纳他人上传文件。

| 阶段 | Skill | 交接标准 |
| --- | --- | --- |
| PPT 引文提取 | `pptx-citation-inventory-zh` | 全部渲染页已核对，原始写法及重复出现页码保留 |
| DOI 与题录核实 | `bibliographic-metadata-resolver-zh` | 每篇作品有已核实身份或明确的未解决原因 |
| 本地 EndNote 检索 | `endnote-pdf-retrieval-zh` | 指定库只读检索，复制件哈希核对 |
| 联网来源查找 | `literature-source-archive-zh` | 未解决文献逐来源核查，PDF 归档注明来源与版本 |
| 英文科研通求助，按需 | `ablesci-literature-assist-zh` | 每次一篇 DOI，核对题录及文件后再决定是否采纳 |
| 论断核验与高亮，按需 | `pdf-claim-highlighter-zh` | 范围内每项论断有判断及证据位置，高亮件已重新检查 |

各阶段沿用稳定的文献/作品 ID，将 PPT 每次引用分开记录。除非用户指定其他顺序，先查指定 EndNote 库，再查联网来源。持续扩展同一清单的阶段字段，保留原文、纠正信息、检索尝试、PDF 来源和版本、未解决状态。“缺 PDF”“有 PDF”“论断有证据”是三种不同状态，不得混同。

中文文献、会议项目与网址引用默认保留为用户自行处理项。标题/DOI 冲突、版本不符、全文不可及要明确列为待处理。最终按实际执行阶段汇总数量、交付物和限制；未执行的阶段不得报告为完成。
