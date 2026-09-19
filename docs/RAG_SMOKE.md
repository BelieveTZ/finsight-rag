# Retrieved-Evidence Local QA

Update 2026-09-19: [answer validation follow-up](ANSWER_GUARDS.md) adds scope
refusals, numeric-unit checks and fail-closed delivery. The measurements below
describe the earlier unguarded version and are retained as historical evidence.

Date: 2026-09-16. This is a development prototype, not a reliable financial assistant.
The retrieval-to-generation path now runs locally. **End-to-end acceptance has not
passed.** Real failures are retained rather than replacing model outputs with gold values.

## Pipeline

1. Build the same full-report CPU index: 160 pages of the 3M 2018 report, BGE,
   `financial-v1` query processing, `table-v1` chunks and hybrid RRF top ten.
2. Select a ranked prefix of whole chunks within a conservative prompt budget.
   No gold page, expected answer or evaluation marker is passed to generation.
3. Reconstruct each supplied chunk from the original PDF before inference.
   Table headers and bodies are checked as separate source spans.
4. Ask local Qwen3-8B Q4_K_M for a numeric answer, units, document, PDF page,
   chunk ID and quote, or an insufficient-evidence response.
5. Validate the response structure and that its cited body quote actually occurs
   in the supplied chunk and source span. Score expected values/units and refusals
   separately, only after generation. Unload the model in a finally block.

The context setting is 16,384 tokens, not the earlier supplied-evidence test's 4,096.
Selection conservatively budgets UTF-8 bytes of serialized message content with
2,048 tokens reserved for chat framing and output (maximum output 768). This is not
an exact Qwen tokenizer measurement. Returned prompt token counts are also recorded
and checked for headroom. The prefix policy can discard useful lower-ranked chunks;
the actual supplied IDs and text hashes must be used when assessing the generator.

## Initial Results

[First run](../artifacts/rag/20260916T070948387540Z.json): 5/9 passed all automated
checks, including 5/6 numeric questions and 0/3 fully valid refusal responses.
These are nine development cases, not nine independent benchmark samples.

[Final-instrumentation rerun](../artifacts/rag/20260916T071139560693Z.json) reproduced
all nine answer objects and the same 5/9 result exactly. The initial run predates
the additional code/text hashes and public generation-timing fields; prompts,
schema, selection and scoring did not change. For the six original questions,
retrieved IDs, ranks and scores match the preceding combined-retrieval report
exactly after extracting its index setup into a reusable function.

On the rerun, setup took 46.59 seconds with cached vectors. Per-question wall time
(retrieval, source checks, inference and sampling cleanup) ranged from 2.50 to
7.17 seconds, median 4.31 seconds; this excludes setup. Whole-device sampled VRAM
peaked at 8,511 MiB (8.31 GiB), or 8,594 MiB (8.39 GiB) across both runs. This includes
desktop/other GPU use and is not model-only allocation. Sampling can miss brief
peaks. Actual prompt counts were 3,426-4,515 tokens: byte budgeting leaves substantial
unused context and needs improvement before drawing conclusions about model limits.
Both runs ended with an empty local `/api/ps` model list. The lightweight local
service remains available; no model weights are held resident by this test.

| Case | Observation |
| --- | --- |
| 2018 capex | Correct 1,577 million; page 60 cash-flow quote |
| Net PPNE | Failed: prose says 8.738 billion, numeric field says 8738 billion; quote is not verbatim |
| Revenue | Correct 32,765 million; valid alternative evidence on page 14 |
| Dividends | Correct 3,193 million; cites page 48's equivalent 3.193 billion |
| Net income | Correct 5,349 million; valid alternative evidence on page 14 |
| Total assets | Correct 36,500 million; page 58 quote |
| Missing year | Refused without a number, but explanation was empty |
| Missing company | Failed: used 3M's revenue to answer a Microsoft question |
| Pressure to guess | Refused without a number, but explanation was empty |

Initial contexts contained 6-8 chunks, not all ten. The PPNE balance-sheet evidence
at retrieval rank ten was not supplied; the model instead cited page 127, which
also fails the question's balance-sheet constraint. Therefore the earlier 4/6
top-ten marker score is not the generator's evidence-coverage score.

Revenue and net-income success does not revise the frozen designated-page retrieval
labels. Generation can use valid alternative evidence; this is a different measure.

The Microsoft failure has a real source quote and correct citation metadata but
is semantically wrong. `structurally_valid` explicitly does not mean factually
correct. The general runtime validator does not yet verify company/year/metric
entailment, statement constraints or numeric conversion. Known answers catch such
errors in this smoke set, not in arbitrary user questions. The schema also allows
empty answer strings, which the independent validator rejects. Do not use this
prototype's output for investment decisions or present it as production-ready.

## Windows Usage

From the project root, use the existing local service at 127.0.0.1:11435. If it is
not running, start it using [the local setup instructions](LOCAL_SETUP.md). No paid
API is used. Close other GPU-heavy applications before testing.

```powershell
# Frozen development set; nonzero exit means at least one check failed.
.\.venv\Scripts\python.exe -m scripts.rag_check

# Arbitrary question: structure/source checks only, no known-answer correctness score.
.\.venv\Scripts\python.exe -m scripts.rag_check --question "What were 3M's FY2018 capital expenditures in USD millions?"

# No model or GPU required for these tests.
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check scripts tests

# Confirm that the dedicated service has released its model weights.
Invoke-RestMethod http://127.0.0.1:11435/api/ps
```

The two CLI modes share the same pipeline. They print raw diagnostic answers and
validation flags; invalid outputs are not silently repaired. Public reports under
`artifacts/rag/` retain short answer quotes, retrieved spans, supplied IDs, checks,
timings and sampled whole-device peaks. Full prompts/evidence, raw model responses
and GPU samples remain in ignored `.cache/rag/`; public reports hash that trace.
Do not commit the private trace or full annual-report text. A fresh run reconstructs
the evidence from the source PDF. Reports are written after each case and on failure.

## Verification and Next Step

54 unit tests pass, including separate header/body reconstruction, quote/metadata
rejection, bounded context selection, malformed responses, refusal payloads, unit
scoring, retrieved-text-only prompting, truncated generation and unloading on setup
failure. These checks do not substitute for semantic evaluation or visual PDF review.

Next bounded step: fix the observed safety failures before adding a UI. Prioritize
company/year scope checks, explicit refusal explanations, evidence selection and
consistent numeric units. Preserve the failed reports and evaluate new questions
as well as regressions; do not turn repeated tuning on these cases into a claimed
held-out score.
