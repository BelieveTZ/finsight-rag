# FinSight-RAG 实施路线图

建议节奏为 6 周、每周 10–15 小时。时间紧时可压缩到 4 周，但不删掉评测与测试。

## Milestone 0：工程起点（0.5 天）

学习：虚拟环境、Python package、命令行入口、单元测试。

任务：

- 安装项目依赖；
- 运行 `finsight doctor`；
- 将 `pyproject.toml` 中的作者改为你的名字；
- 初始化 Git，完成第一笔提交。

验收：`finsight doctor` 与 `pytest` 均成功。

## Milestone 1：文档数据管道（3–5 天）

学习：PDF 文本/表格解析、页码元数据、清洗、chunking、数据质量。

任务：

- 选择 5–10 份公开年报，记录来源与许可；
- 解析为带 `document_id/page/section/text` 的 JSONL；
- 比较固定长度、递归和标题感知三种切分；
- 建立 30–50 条人工问题及标准证据页。

验收：同一输入可重复生成一致数据；随机抽查 50 个 chunk，记录解析错误率。

## Milestone 2：检索基线（4–6 天）

学习：BM25、embedding、cosine similarity、Recall@K、MRR。

任务：

- 分别实现 sparse 与 dense retrieval；
- 用 RRF 融合两路结果；
- 对 chunk 大小、overlap、top-k 做消融；
- 输出 CSV/JSON 指标和可视化图表。

验收：一条命令复现实验；混合检索相对最佳单路基线有可解释的结果（提升或失败原因）。

## Milestone 3：重排与可引用生成（4–6 天）

学习：cross-encoder、prompt contract、结构化输出、groundedness、拒答。

任务：

- 在 top-k 候选上加入 reranker；
- 答案必须返回引用页码和证据 ID；
- 构造“文档中无答案”的问题并测试拒答；
- 记录准确率、引用命中率、拒答准确率与延迟。

验收：展示至少 3 个升级成功案例和 3 个失败案例。

## Milestone 4：工具调用 Agent（4–6 天）

学习：tool schema、状态机、错误恢复、可观测性。

任务：

- 实现计算器和同比/环比工具；
- 区分“直接检索问答”和“检索后计算”；
- 记录每一步工具输入输出，设置最大步数与超时；
- 为工具选择、参数和最终答案编写测试。

验收：在数值问题集上，Agent 明显优于纯文本生成基线，并能解释计算过程。

## Milestone 5：服务化与作品集包装（5–7 天）

学习：FastAPI、异步请求、缓存、Docker、CI、演示表达。

任务：

- 提供 API 和简洁 Web 界面；
- 加缓存、错误处理、健康检查与基础限流；
- 容器化并配置 GitHub Actions；
- 完成中英文 README、架构图、Demo GIF、实验报告；
- 整理 3 分钟项目介绍和 10 个高频追问。

验收：陌生人按照 README 能在 10 分钟内跑通最小 Demo；所有测试与 CI 通过。

## 可选加分项（完成主线后再选一个）

- 用 LoRA 微调轻量 reranker，并与零样本模型公平对比；
- 增加 query rewriting，但必须用消融实验说明收益；
- 用 vLLM 部署开源模型，展示吞吐/显存/延迟曲线；
- 增加多模态表格/图表理解；
- 把错误案例整理为公开小型 benchmark。

## 每周作品证据

每周至少保留：一个可运行版本、一张指标表、一页错误分析、一条规范 commit。不要在最后一天集中补记录。

