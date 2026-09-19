# Six-Case Demonstration Protocol

The original specification requires two numeric facts, two business/risk facts and
two refusals, all genuinely run and manually checked. Earlier numeric-only progress
does not waive this requirement. `evaluation/demo_v1.json` fixes six exposed
development questions before qualitative model runs. It is not the final benchmark.

## Report-Fact Mode

Select **Report fact** in the local workspace. The report, company and one explicit
report year must match the selected document. Retrieval still searches the complete
PDF and the generator sees only bounded retrieved chunks. No labels or expected
pages are included in the model request.

Unlike numeric mode, an answered fact has a null numeric value and empty unit. The
model selects a short verbatim excerpt (at most 600 characters) and cites a supplied
chunk. Source-span and quote checks remain mandatory. The displayed answer uses
that exact excerpt, not an unchecked paraphrase. This helps traceability but cannot
prove that the excerpt actually answers the question; manual review remains a gate.

The numeric prompt, numeric schema and numeric validation remain separate and are
not relaxed to accept text. The 30-case numeric/refusal portfolio set is unchanged.

## Accepted Cases

| Case | Report | Type | Source review |
| --- | --- | --- | --- |
| 2018 capex | 3M 2018 | Numeric | Cash-flow statement, PDF 60 |
| 2022 operating cash flow | PepsiCo 2022 | Numeric | Cash-flow statement, PDF 64 |
| Frito-Lay North America products | PepsiCo 2022 | Business fact | FLNA section, PDF 5 |
| Limited/sole-supplier risk | PepsiCo 2022 | Risk fact | Supply-chain risk, PDF 17 |
| 2024 revenue in a 2018 report | 3M 2018 | Refusal | Out-of-period scope rejection |
| Revenue from Microsoft alone | PepsiCo 2022 | Refusal | Undisclosed customer-level figure |

The [accepted model run](../artifacts/demo/20260919T065722467425Z-generation.json)
was reviewed against original pages: **6/6 demonstrations accepted, 4/4 answered
citations supported**. The capex answer uses valid alternative PDF page 46 rather
than annotated page 60; the question did not constrain statement type. Labels were
not changed. See [the case-by-case source review](SOURCE_REVIEW.md).

The [first run](../artifacts/demo/20260919T065350455654Z-generation.json) passed the
automatic checks but failed the FLNA semantic review: its quote included Quaker
Foods products. A fact-only prompt follow-up requests short, complete sentences for
the requested entity. The rerun produced the relevant FLNA excerpt. Both runs are
retained; six exposed demonstrations do not establish general fact-QA accuracy.

## Commands

CPU-only retrieval check, no Ollama calls:

```powershell
.\.venv\Scripts\python.exe -m scripts.fact_retrieval_check
```

Only after GPU availability is confirmed and the local Ollama service is started:

```powershell
# Run all six fixed demonstrations and retain the actual output.
.\.venv\Scripts\python.exe -m scripts.demo_check --allow-gpu

# Optional single-question diagnosis.
.\.venv\Scripts\python.exe -m scripts.rag_check --document PEPSICO_2022_10K --answer-kind fact --question "According to PepsiCo's FY2022 report, what kinds of products does Frito-Lay North America sell?"
.\.venv\Scripts\python.exe -m scripts.rag_check --document PEPSICO_2022_10K --answer-kind fact --question "What supply-chain risk involving limited suppliers does PepsiCo describe in its FY2022 report?"
```

Use the remaining questions from the manifest in numeric mode, and then run one
new non-preset question interactively. The command records actual output under
`artifacts/rag/` and private prompt traces under `.cache/rag/`, unloading the model
at completion. Interactive exit zero means structural checks succeeded, not that
the question was answered correctly. Record relevance, exact source, correct company
and period, and any alternative evidence page explicitly.

Status: real local generation and source review are complete for the six fixed
cases. The CPU-only viewer replays this accepted run and labels it as saved.
Replaying it is not a new inference run. No paid API was used.

The six-case runner writes `artifacts/demo/*-generation.json`, with full private
traces in `.cache/demo/`. It requires explicit GPU opt-in and unloads on completion
or failure. `automatic_check_passed` is not a semantic score: the two qualitative
cases still require source review for relevance and completeness. Incomplete and
failed runs remain visible; no known-good text is substituted for live output.

## CPU Evidence-Selection Experiment

Original pages 5 (printed 3) and 17 (printed 15) were visually inspected. The first
[retrieval run](../artifacts/demo/20260919T062000561673Z-fact-retrieval.json) found
the FLNA page with both methods. For supplier risk, dense missed the annotated page
and hybrid ranked it eighth; the byte budget cut off context before that candidate.
The failure is retained, and the question and gold page were not rewritten.

The candidate `branch-champions-v1` policy, applied only to report-fact mode, promotes
each retrieval branch's first-ranked candidate **within the already returned top 10**.
It preserves original chunks and the same context byte limit. It does not inspect
gold pages, answer labels or pages outside the retrieval result. Remaining candidates
retain their order. Explicit `ranked-prefix` mode still provides the old control.

The [follow-up CPU run](../artifacts/demo/20260919T062400022446Z-fact-retrieval.json)
kept the same retrieval ranks but included the risk page in hybrid context. On these
two exposed examples, selected gold-page coverage changed from 1/2 to 2/2 for hybrid
and stayed 1/2 for dense. The actual selected risk chunk includes the limited/sole-
supplier paragraph. This does not show answer accuracy or broad retrieval improvement;
champion preservation can also promote a noisy lexical match. The subsequent GPU
demonstration results and limitations are recorded above.
