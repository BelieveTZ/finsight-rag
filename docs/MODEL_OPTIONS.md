# FinSight-RAG 首版模型选择

**检索实测补充（2026-09-16）：** 已使用 BGE-small-en-v1.5 的 Qdrant 量化 ONNX 版本在 CPU 上验证全文检索，未安装 PyTorch；这是低依赖量的运行时调整，不是原先全精度 Sentence Transformers 路径的实测。结果与限制见 [全文检索验证](RETRIEVAL_CHECK.md)，重排仍未验证。

**后续实测（2026-09-16）：** Qwen3-8B 的本地环境与给定证据问答已完成验证，结果及拒答格式修正见 [本机验证报告](LOCAL_VALIDATION.md)。下文保留 2026-09-15 的选型快照；嵌入、重排与完整 RAG 仍未验证。

核验日期：2026-09-15。范围：六天内交付英文财报 QA 作品，GitHub 展示与本地 Demo。仅核对发布者模型卡及运行时官方文档；未下载、安装模型，未运行 CPU/GPU 推理，未调用付费 API。硬件信息与本机安装状态见主任务的 [硬件检查](HARDWARE_CHECK.md)，本文不重复检查。

## 1. 推荐固定配置

以下为工程建议，尚非本机验证结果。嵌入与重排明确指定 CPU；GPU 空闲后再验证生成。主任务已确认当前 GPU 忙碌、未发现独立 Python/Ollama，内置 Python 3.12.14 无 torch，因此此方案需要后续准备运行环境，当前不能直接启动；可用内存也不能按总内存计算。六天窗口内优先完成检索对比、证据引用和失败案例，不扩展模型选型。

| 环节 | 准确模型标识与设备 | 官方规格与限制 | 许可 |
| --- | --- | --- | --- |
| 英文嵌入 | `BAAI/bge-small-en-v1.5`，CPU | 33.4M 参数；384 维；最大序列 512 tokens；单个 safetensors 权重约 133 MB | MIT |
| 英文重排 | `cross-encoder/ms-marco-MiniLM-L6-v2`，CPU | 22.7M 参数；6 层；位置上限 512 tokens，问题与段落合计需计入特殊 token；单个 safetensors 权重约 90.9 MB | Apache-2.0 |
| 本地生成 | Qwen `Qwen3-8B`；Ollama `qwen3:8b-q4_K_M` | 官方模型约 8.2B 参数；Ollama 标注 8.19B、Q4_K_M、约 5.2 GB；Qwen 原生上下文 32,768 tokens，YaRN 扩展至 131,072，但首版只配置 4096，验证后再考虑 8192 | Apache-2.0 |

来源：[BAAI 模型卡](https://huggingface.co/BAAI/bge-small-en-v1.5)、[BAAI 权重目录](https://huggingface.co/BAAI/bge-small-en-v1.5/tree/main)、[重排模型卡](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2)、[重排配置](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2/raw/main/config.json)、[重排权重目录](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2/tree/main)、[Qwen 模型卡](https://huggingface.co/Qwen/Qwen3-8B)、[Ollama 精确量化标签](https://ollama.com/library/qwen3:8b-q4_K_M)。

注意名称是 `MiniLM-L6-v2`，不是 `MiniLM-L-6-v2`。重排配置内遗留的 `_name_or_path` 含 `L-12`，但同文件的 `num_hidden_layers` 是 6；应使用上表发布仓库标识。模型文件大小不等于安装总量、内存占用或显存占用。

## 2. 运行方式与输入预算

- **CPU 检索组件：** 使用 Sentence Transformers 的 `SentenceTransformer` 和 `CrossEncoder`，均显式设 `device="cpu"`，不使用自动设备映射。官方接口支持 CPU，PyTorch 官方提供 Windows 无 CUDA 路径，因此 Windows 11 的运行路线有官方依据；本机依赖兼容性仍待检查。[嵌入接口](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html)、[重排接口](https://www.sbert.net/docs/package_reference/cross_encoder/model.html)、[PyTorch Windows 支持](https://pytorch.org/get-started/locally/)
- **切分建议：** 先以约 300-400 个嵌入 tokenizer tokens 为正文块预算，逐模型检查问题、前缀与特殊 token 后的长度，避免重排截断关键数字。BGE 查询采用官方短查询检索前缀 `Represent this sentence for searching relevant passages: `，正文不加此前缀，向量归一化。块大小为项目起点，不是官方最佳值。[BAAI 使用说明](https://huggingface.co/BAAI/bge-small-en-v1.5)
- **生成运行时：** Ollama 原生支持 Windows 和 NVIDIA GPU，官方要求 Windows 10 22H2 或更新、NVIDIA 驱动 551.61 或更新；本地 API 默认地址为 `http://localhost:11434`。操作系统支持不等于本机已安装或驱动已合格。[Ollama Windows 文档](https://docs.ollama.com/windows)
- **关闭思考：** Ollama 原生 chat/generate 请求显式使用 `think: false`；不要把 Transformers 的 `enable_thinking=False` 当作 Ollama 请求参数。Qwen 官方也支持非思考模式。[Ollama thinking 文档](https://docs.ollama.com/capabilities/thinking)、[Qwen 模型卡](https://huggingface.co/Qwen/Qwen3-8B)
- **上下文建议：** 显式配置 `num_ctx=4096`，输出预算先设约 512 tokens；提示、检索证据和输出共用窗口。只有证据预算需要且实测稳定时再改为 8192。增大上下文会增加内存需求；当前官方页面对默认值的描述不同，因此不依赖默认值。[Ollama 参数](https://docs.ollama.com/modelfile)、[上下文说明](https://docs.ollama.com/context-length)

**硬件适配判断（推断）：** 在用户给定的 12GB 显卡、32GB RAM 条件下，5.2GB 量化权重配短上下文值得作为首选验证方案，但不能据此保证完全驻留 GPU 或给出总占用值。运行还需 KV cache、计算缓冲与其他进程空间；GPU 当前被占用，等待空闲后再验证加载、实际上下文和 CPU/GPU 分配。本文没有首 token 延迟、tokens/s、CPU 重排耗时或质量提升的实测结论。

## 3. 唯一可选 API：GPT-4.1 mini

可选生成替代为 `gpt-4.1-mini`，复现实验可固定 `gpt-4.1-mini-2025-04-14`。官方窗口为 1,047,576 tokens，最大输出 32,768 tokens；无需为本项目使用其完整窗口。它是托管 API，不能按上述开放权重模型的许可和本地运行方式处理。[OpenAI 官方模型文档](https://developers.openai.com/api/docs/models/gpt-4.1-mini)

核验当日标准文本价格（USD/百万 tokens）：输入 **$0.40**，缓存输入 **$0.10**，输出 **$1.60**。以下按普通未缓存请求计算，不使用 Batch 折扣。[OpenAI 官方价格](https://developers.openai.com/api/docs/pricing)、[模型价格](https://developers.openai.com/api/docs/models/gpt-4.1-mini)

| 示例 | token 数 | 费用 |
| --- | --- | --- |
| 120 次，每次 4000 输入 | 480,000 | $0.192 |
| 120 次，每次 500 输出 | 60,000 | $0.096 |
| 合计 | 540,000 | **$0.288 USD**，约 $0.29 |

这是算术估算，不是实际账单。假设 4000 输入已包含系统提示、问题、证据及历史；不含重试、额外评测、工具调用或税费。API 仅作可选方案，未核验账户权限或余额，未发送请求。首版建议默认本地生成，API 由明确配置启用，运行失败时不自动转为付费调用。

## 4. 交付边界

本方案是通用英文检索与生成基线，尚未验证财报表格、年份、单位和数字的准确率。作品中的速度、质量与重排收益只填写后续真实评测结果；GitHub 保留模型标识、版本与许可链接，演示材料区分本地模型与 API 的结果。
