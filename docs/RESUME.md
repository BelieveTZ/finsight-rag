# 简历描述与使用边界

适用定位：AI 应用、RAG、LLM 工程与 Python 后端方向的求职作品。
这是本地研究原型，不是模型训练项目或生产级财务系统。以下指标来自
[冻结评测](PORTFOLIO_EVALUATION.md)和[逐条来源复核](SOURCE_REVIEW.md)。

## 中文版本

**FinSight-RAG｜本地英文财报证据问答系统**

- 基于 Python、Qwen3-8B、BGE 与 BM25/RRF 构建本地财报 RAG 流程，索引 4 份完整财报共 997 页、2,245 个片段，支持数值问答、原文摘录、页级引用与证据查看。
- 建立按文档隔离的 24 道数值题与 6 道拒答题评测；在固定 12 题最终数值集上，纯向量与混合检索分别匹配 5/12、9/12，进一步分离引用支持、误拒答和检索指标，保留逐题结果与失败分析。
- 在 12 GB 显存设备上完成六条真实演示及隔离环境复现，提供本地交互界面、Windows 操作说明和 127 项测试；推理不使用收费 API。

篇幅有限时保留前两条；不要只写“准确率提升 80%”而省略样本数和评测规则。
更严格的“数值匹配且有直接引用支持”是纯向量 5/12、混合 8/12。

## English Version

**FinSight-RAG | Local Evidence-Grounded Financial QA**

- Built a local financial-report RAG pipeline with Python, Qwen3-8B, BGE embeddings and BM25/RRF, indexing 997 pages across four reports with page-level citations and source inspection.
- Evaluated dense and hybrid retrieval on a document-separated set of 24 numeric questions and six refusal probes; recorded 5/12 versus 9/12 fixed-target numeric matches on the final split, with separate citation review and failure analysis.
- Delivered six source-reviewed demonstrations, a local evidence workspace, 127 tests and an isolated-environment reproduction on a 12 GB GPU, without paid inference APIs.

## 面试时必须能解释

1. 检索负责找材料，生成负责据材料作答；检索命中并不保证回答正确。
2. RRF 合并的是排名，不是直接相加不同检索器的原始分数。
3. 固定标签数值匹配 9/12，不等于九条都有直接、充分的证据支持。
4. 最终集仅两份文档、12 道数值题，没有独立标注者，不能代表一般财报问答表现。
5. 拒答题中包含程序规则拦截；不能把它们全算作模型拒答能力。
6. 本项目调用已有量化模型，没有训练、微调、OCR、重排器或在线部署。

建议从一个成功例子和一个失败例子讲起：3M 现金余额 2,853 的正确引用；
CVS 每股收益 3.16 被误当作总净利润的失败。理解这两条完整路径后，再展开实现细节。
不熟悉的模块如实说明正在补基础，不需要宣称独立掌握全部算法或财务知识。
