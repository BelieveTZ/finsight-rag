# Local Qwen3-8B Validation

Subsequent work: [full-report CPU retrieval has now been tested](RETRIEVAL_CHECK.md).
This document preserves the earlier generation-only experiment and its boundaries.

Date: 2026-09-16. Final run: 05:49:42-05:50:10 UTC, or 13:49-13:50 China Standard
Time (UTC+8). This is a development smoke test with supplied evidence, not a RAG
benchmark, held-out evaluation, or financial-advice quality assessment.

**Decision:** keep Qwen3-8B Q4_K_M as the local generation baseline for the first
release. It fits this machine and handles these simple evidence questions and
refusals with a constrained response schema. No paid API was called.

## Environment

| Component | Verified configuration |
| --- | --- |
| OS | Windows 11, build 26200 |
| CPU / RAM | Ryzen 7 7800X3D / 32 GB nominal |
| GPU | RTX 4070 SUPER, 12,282 MiB reported VRAM |
| NVIDIA driver | 595.71 |
| Python / uv | 3.12.14 / 0.12.15, project-local installations |
| Ollama | 0.34.1, standalone Windows runtime |
| Model | `qwen3:8b-q4_K_M`, 8.2B, GGUF Q4_K_M |
| Inference | 100% GPU reported by `ollama ps`; 4096 context tokens |
| Request options | `think=false`, temperature 0, seed 42, maximum output 512 tokens |
| Endpoint | `127.0.0.1:11435`; `OLLAMA_NO_CLOUD=1`; no remote fallback |

Model manifest digest:
`500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
The portable runtime archive was verified against its published SHA-256 before use.
Tools, model weights, dataset cache and virtual environment are excluded from Git.
Only the validation script needs Python; no Python ML stack was installed.

## Evidence and Cases

Input: FinanceBench `financebench_id_03029`, document `3M_2018_10K`, annotated PDF
page 60 (1-based). The entire annotated cash-flow page was supplied to the model,
not retrieved. Expected answers were used by the checker only, not sent to the model.
The original PDF was not independently inspected during this test.

Dataset SHA-256:
`a5a2aa673e573e55675fc3c0f9aa38c1cf59d2abc91edb077534f71f10a71877`.
Evidence text SHA-256:
`ef08f278890e3791af040de7320578a604b1daaa32a83dee60aef263d4d0044d`.
Source URL and full prompts/schemas are retained in both raw reports below.

| Case | Expected behavior | Initial run | Final run |
| --- | --- | --- | --- |
| FY2018 capital expenditures | 1,577 USD millions, document/page/quote | 3/3 | 3/3 |
| FY2017 capital expenditures | 1,373 USD millions, document/page/quote | 3/3 | 3/3 |
| FY2018 dividends | 3,193 USD millions, document/page/quote | 3/3 | 3/3 |
| FY2024 capital expenditures | Refuse: year absent | 0/3 | 3/3 |
| FY2018 revenue | Refuse: metric absent | 3/3 | 3/3 |
| FY2024 revenue, asked to guess | Refuse despite pressure | 0/3 | 3/3 |
| Strict combined checks | Six distinct cases, repeated three times | 12/18 | 18/18 |

The initial model refused all nine unanswerable requests and invented no amounts.
However, six refusals returned `pdf_page: 0` rather than `null`. Those failed the
existing citation contract; they are not counted as passes.

The only generation change was a status-dependent `oneOf` JSON schema: an answered
response requires numeric value and citation fields, while a refusal requires null
value/document/page and empty unit/quote. The prompt, cases, expected answers,
model and inference options did not change. Outputs were not repaired after generation,
and the checker was not relaxed. Two regression tests cover the observed failure
and the new constraint. The final result is for this constrained generation setup,
not unconstrained model behavior. The same development cases were reused to verify
the fix; this is not independent evidence of generalization.

All 36 raw answers were inspected. Answered values match the supplied year columns,
units and cash-flow rows; quotes match after whitespace normalization. Final refusals
contain no guessed number or invented citation. Two refusal explanations are generic
("not answerable from this evidence") rather than specifying the missing year/metric;
improving this wording remains a usability task, not a fabricated-answer finding.

## Timing and VRAM

| Measurement | Initial run | Final run |
| --- | --- | --- |
| First request, weights initially unloaded | 49.790 s | 4.093 s |
| Ollama reported load duration within first request | 23.336 s | 2.015 s |
| Subsequent 17 requests, median full-response time | 1.041 s | 1.054 s |
| Subsequent requests, minimum-maximum | 0.885-1.943 s | 0.895-1.948 s |
| Median output generation rate, subsequent requests | 68.42 tokens/s | 68.14 tokens/s |
| Baseline whole-device used VRAM | 752 MiB | 743 MiB |
| Sampled peak whole-device used VRAM | 6,293 MiB | 6,263 MiB |
| Minimum sampled free VRAM | 5,705 MiB | 5,735 MiB |
| Ollama loaded-model `size_vram` | 5,578,204,118 bytes | 5,578,204,118 bytes |
| Used VRAM after unloading | 709 MiB | 709 MiB |
| GPU samples / sampling errors | 303 / 0 | 118 / 0 |

Interpretation: peak whole-device usage was about **6.15 GiB**, while Ollama reported
about **5.20 GiB** for the loaded model. These are different measurements. Desktop
processes also used the GPU; the peak is not exclusively attributable to the model.
The free/used sum can differ from total VRAM because of driver-reserved memory.
There was roughly 5.6 GiB of sampled free VRAM in this specific short-context run;
this is not a promise about concurrent workloads or longer contexts.

The 49.790-second first-ever request includes initial runtime/model warm-up as well
as answering. The second run unloaded weights but reused the same server and had
already exercised the GPU/runtime and OS caches, so its 4.093-second reload must not
replace the first-use figure. Warm times can also benefit from shared prompt caching.
Wall time measures a complete non-streamed response, not time to first token.
Input counts were 1,712-1,726 tokens, outputs 58-129 tokens. These results do not
predict long-answer, long-context, concurrent-user or full-RAG latency.

VRAM sampling waits 0.2 seconds between `nvidia-smi` calls plus command overhead;
short spikes may be missed. Output tokens/s uses Ollama's `eval_count / eval_duration`,
not total request duration. Both runs completed without API or unload errors.
After the final run, `/api/ps` confirmed no loaded model and free VRAM was 11,289 MiB.
The loopback server remains available but holds no model weights.

## Reproduce and Inspect

- [Windows setup and run instructions](LOCAL_SETUP.md)
- [Initial raw report, including failures](../artifacts/local-smoke/20260916T054734960325Z.json)
- [Final raw report](../artifacts/local-smoke/20260916T054942137812Z.json)
- [Validation script](../scripts/local_smoke.py)
- [Checker regression tests](../tests/test_local_smoke.py)

Verification: 9 unit tests passed, Ruff lint and formatting checks passed, PowerShell
startup script parsed and ran successfully, and `uv sync --locked --offline` verified
the prepared dependency environment. No paid service credentials were required.

Next bounded step: ingest a small financial-report corpus, retain page provenance,
and test whether retrieval finds the correct evidence before connecting this generator.
Keep this document and these questions in the development/demo split. Embeddings,
reranking, PDF ingestion, retrieval metrics and UI behavior remain unverified.
