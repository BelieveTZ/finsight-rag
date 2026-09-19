# Portfolio Evaluation

Status, 2026-09-19: development and frozen document-separated final generation
completed locally. All failures are retained. The main result is a small authored
evaluation, not an official FinanceBench score or proof of production readiness.

## Questions and Split

The [corpus record](CORPUS.md) explains the selection and visual label review.
`evaluation/portfolio_v1.json` contains 24 numeric questions and six refusals:

| Split | Reports | Numeric | Refusal |
| --- | --- | ---: | ---: |
| Development | 3M 2018, PepsiCo 2022 | 12 | 3 |
| Final | AMD 2022, CVS Health 2022 | 12 | 3 |

These are mostly authored questions, not an official FinanceBench benchmark.
Source tables were inspected for annotation before running the new experiments.
Question selection was not based on model success. Runtime corpus metadata does
not contain gold answers or evidence pages. Each method sees the same questions,
complete document index, model and context budget.

## Completed Generation Results

Raw reports: [initial development](../artifacts/portfolio/20260919T064443995840Z-development-rag.json),
[development follow-up](../artifacts/portfolio/20260919T064925054509Z-development-rag.json),
[frozen final](../artifacts/portfolio/20260919T070257595016Z-final-rag.json).
Source decisions: [per-case review](SOURCE_REVIEW.md). Failures:
[analysis](FAILURE_ANALYSIS.md). The final set was run once; no final-driven tuning.

| Metric | Dense | Hybrid |
| --- | ---: | ---: |
| Initial development numeric target matches | 9/12 | 9/12 |
| Follow-up development numeric target matches | 11/12 | 11/12 |
| Final numeric target matches | **5/12** | **9/12** |
| Final target match AND direct citation support | **5/12** | **8/12** |
| Final directly supported / delivered citations | 5/7 | 8/11 |
| Missing citations on delivered factual answers | 0 | 0 |
| Final false refusals / answerable questions | 5/12 | 1/12 |
| Final correct refusals / refusal probes | 3/3 | 3/3 |
| Final service/run errors / all requests | 0/15 | 0/15 |
| Final gold-page Recall@5 | 5/12 | 3/12 |
| Final gold-page Recall@10 | 5/12 | 7/12 |
| Final MRR@10 | 0.1597 | 0.2288 |
| Final gold-page field/number marker hit@10 | 4/12 | 6/12 |
| Final selected-context marker hit | 3/12 | 4/12 |

Numeric target match uses exact unit plus absolute value tolerance 0.0001 and
requires structural/source validation to pass. All twelve answerable questions
remain in each denominator. Citation review separately checks the requested
fact. Hybrid's nine numeric matches include one indirect assets citation; its
eleven delivered citations also include a definition-sensitive PP&E answer and
an unsupported capex answer. Neither indirect nor ambiguous evidence is counted
as direct support. The PP&E note genuinely includes held-for-sale assets while
the fixed target excludes them. Labels and scores were not silently revised.

Each method's three refusals comprise two programmatic scope checks and only one
in-scope model refusal. Both development methods also pass 3/3 refusal probes.
This small set cannot establish general refusal robustness. Alternative valid
pages explain some answers whose fixed gold-page retrieval scores are zero.

The numeric prompt follow-up requests complete metric qualifiers, self-contained
units and quotes in the exact cited chunk. It also slightly increases prompt
bytes, so the shared byte budget can change supplied context: this is not a pure
generation-only ablation. Hybrid's development selected-marker count became 9/12,
while its gold-page retrieval count stayed 10/12. The later fact-only prompt edit
changed `rag.py`'s hash but not the numeric prompt/schema/options or numeric branch.
The freeze was made after that edit and the six-case source review. Final pipeline
hashes still match [the frozen configuration](../evaluation/portfolio_config.json).

## Runtime and Cost

Final run, RTX 4070 SUPER 12 GB, Windows, Qwen3-8B Q4_K_M, context 16,384, temperature
0, seed 42, thinking off; CPU BGE embeddings. Ollama 0.34.1 and model digest are
recorded in the report. Every question runs serially, dense before hybrid.

| Final timing | Dense | Hybrid |
| --- | ---: | ---: |
| Search p50 / p95 (13 searches each) | 7.87 / 9.00 ms | 9.40 / 11.99 ms |
| Question wall p50 / p95 (15 each, including scope refusals) | 3.63 / 20.44 s | 3.93 / 6.15 s |
| Warm generated-question wall p50 / p95 | 3.66 / 4.90 s (n=12) | 4.16 / 6.66 s (n=13) |

The first dense request took 55.48 s from an unloaded model; hybrid benefited from
the existing loaded model. Therefore the all-request p95 difference is **not** a
fair claim of method speedup. Warm means reported model load duration <=1 second,
not a cold disk-cache or randomized benchmark. Timings exclude CPU index setup:
31.58 s for AMD and 70.64 s for CVS, with cached vectors and full PDF extraction.
Small-sample p95 is descriptive only; this is response completion, not first-token time.

Final run totals: 99,187 prompt tokens, 3,559 output tokens, 26 actual generation
calls and four scope skips, zero retries. Sampled peak **9,486 MiB whole-device
VRAM** (about 9.3 GiB), zero sampling errors. Other desktop processes are included;
sampling can miss brief peaks. This is not the model's isolated allocation.
Unloading was verified. Average paid API cost is **USD 0 per question**, using
only the fixed local endpoint; electricity/hardware cost was not measured.

The separately verified first browser question took 120.85 s including its CPU
index setup and unloaded-model startup. Do not advertise warm four-second batch
latency as first-use interactive latency.

## CPU Development Results

Raw run: [20260919T053901804375Z](../artifacts/portfolio/20260919T053901804375Z-development-retrieval.json).
Denominator is the 12 answerable questions, not 30 method executions.

After adding the separate report-fact mode, a
[CPU regression run](../artifacts/portfolio/20260919T062535590616Z-development-retrieval.json)
completed all 30 method executions. Per-case retrieval metrics and supplied chunk
IDs were compared with the earlier run and are unchanged. This checks retrieval
compatibility only, not model-generation equivalence. The table below retains the
original timing measurements rather than replacing them with the faster rerun.

| Metric | Dense | Hybrid (BM25 + dense, RRF) |
| --- | ---: | ---: |
| Gold-page Recall@5 | 8/12 | 7/12 |
| Gold-page Recall@10 | 9/12 | 10/12 |
| MRR@10 | 0.4750 | 0.4696 |
| Gold-page field/number marker hit@10 | 9/12 | 10/12 |
| Selected-context marker hit | 9/12 | 10/12 |
| Search latency p50 / p95 | 8.02 / 13.16 ms | 11.10 / 15.00 ms |

Search timings include query embedding and retrieval, exclude index setup and
generation, and use 15 questions per method including refusal probes. Dense runs
before hybrid for each question; this is not a randomized performance benchmark.
Hybrid has better Recall@10 here, but worse Recall@5 and slightly worse MRR. Do not
claim a universal improvement. PepsiCo is 6/6 for both methods; 3M is 3/6 dense and
4/6 hybrid. Small sample size and exposed development questions limit conclusions.

Gold-page recall only asks whether the annotated PDF page appears. Marker hit
additionally requires predefined text/number strings in one chunk on that page.
Neither proves the model answered correctly or that the quote semantically supports
the answer. Valid alternative pages can be penalized by the fixed labels; report
such cases separately instead of changing labels after seeing the result.

## Generation Protocol

1. Finish development-only evidence selection and generation checks.
2. Freeze configuration, question/corpus hashes, prompts, schema and pipeline hashes.
3. Run final dense and hybrid evaluations once under that unchanged configuration.
4. Keep errors and false refusals in the denominator. Inspect actual cited rows,
   columns, year, company and unit; record semantic support separately from automated
   quote matching. Do not call regex/unit checks a semantic correctness judge.
5. If final results lead to changes, label the follow-up exploratory, not held out.

The frozen file is created exclusively, not overwritten. The final runner rejects
missing or changed configuration. That guard does not make the small authored set
statistically representative or independently annotated.

```powershell
# No GPU or Ollama calls.
.\.venv\Scripts\python.exe -m scripts.portfolio_eval --split development --stage retrieval

# Only after confirming the GPU is available and starting the dedicated Ollama service.
.\.venv\Scripts\python.exe -m scripts.portfolio_eval --split development --stage rag --allow-gpu

# Freeze only when development decisions are complete.
.\.venv\Scripts\python.exe -m scripts.portfolio_eval --freeze
.\.venv\Scripts\python.exe -m scripts.portfolio_eval --split final --stage rag --allow-gpu
```

Reports go to `artifacts/portfolio/`; full prompt traces stay in ignored
`.cache/portfolio/`. Exit zero means the experiment completed without service/run
errors, **not** that every answer passed. Read the per-case `passed` and summary
fields. API cost is zero; electricity and hardware depreciation are not measured.
Current generation runs also record sampled whole-device VRAM during each question
and verify unloading. These readings include other processes, can miss short peaks
and are not per-process allocations. Interrupted runs are marked incomplete; do
not publish their smaller partial denominator as a completed score.

## Evidence Selection Development

The prior guarded ranked-prefix run passed 8/9 exposed 3M checks, including three
programmatic scope refusals. PP&E was refused after validation and remained a failure.

The [statement-first run](../artifacts/rag/20260919T051933127591Z.json) passed 7/9:
promoting statement chunks brought the missing balance-sheet evidence into context,
but did not make the model select it. Capex cited an unwanted statement; PP&E used
the wrong page and unit. Both outputs failed checks. This regression is retained.

`statement-filtered` keeps only retrieved chunks with the explicitly requested
statement heading. It does not read gold labels or scan missing pages as a fallback.
Its initial follow-up was interrupted for GPU coordination. After explicit GPU
confirmation, the [first completed filtered run](../artifacts/rag/20260919T063902498787Z.json)
passed 8/9: the correct PP&E value and page were rejected because the validator did
not recognize the PDF heading `Consolidated Balance Shee t`. Selection already
recognized that spelling. This was a validation false refusal, not a retrieval miss.

Selection and validation now share the same full-line, whitespace-normalized heading
recognizer; a narrative mention still does not qualify. Regression tests cover the
split heading. The [rerun](../artifacts/rag/20260919T064217520439Z.json) passed **9/9**:
six numeric answers and three programmatic scope refusals. This is exposed development
evidence, not held-out accuracy. The sampled whole-device peak was 9,406 MiB; CPU
setup took 52.56 s, the unloaded-model first request 58.51 s, and the remaining five
generated requests 2.67-4.79 s. The model was confirmed unloaded after the run.

The source-page review confirmed capex on PDF 60, net PP&E and assets on PDF 58,
revenue and income on PDF 14, and dividends on PDF 48. PDF 14 and 48 are valid
alternative evidence pages for unconstrained questions; gold labels were not changed.
The schema also removes duplicate `chunk_id` required entries. Historic reports,
including the 7/9 regression and 8/9 false-refusal run, remain unchanged.
