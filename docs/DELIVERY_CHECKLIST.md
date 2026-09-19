# Portfolio Delivery Acceptance

Updated 2026-09-19. Delivery scope: a reproducible portfolio research prototype.
No paid inference or hosted deployment. Retain all failures and development reports.

GPU coordination: before **every new GPU work session**, confirm that other training
has stopped and sufficient memory is free. CPU-only indexing, tests and documentation
do not require the model service. An earlier statement-filtered follow-up was
interrupted for resource coordination; the model was unloaded and its server stopped.

## Deliverable Scope

Deliver a **local financial-QA research prototype** with numeric evaluation and
extractive business/risk demonstrations. Use the specification's permitted
four-document/two-retriever reductions, not an easier replacement acceptance gate.
The earlier numeric-only implementation was an intermediate state. The original
six real demonstration cases remain required: two numeric facts, two business/risk
facts and two refusals. General accounting reasoning remains out of scope. Do not
claim the larger standard v1 data scale or three-retriever experiment is complete.

Required before resume readiness:

- [x] Complete the statement-aware evidence-selection experiment without relaxing checks.
- [x] Support a fixed four-document corpus with full-PDF ingestion and pinned sources.
- [x] Freeze at least 20 numeric questions with document-separated development and
      final evaluation, plus six documented unanswerable cases. Preserve source
      labels separately from runtime inputs. Explain any authored vs official cases.
- [x] Compare dense and hybrid retrieval with the same context/model budget;
      retain mistakes, refusals, citation checks, latency and resource measurements.
- [x] Inspect actual cited evidence and report semantic support separately from
      string matches. Record all failures, including at least three historic cases.
- [x] Provide a usable local question/evidence workflow, error states and a way to
      open cited PDF pages. No internet-facing service or paid endpoint.
- [x] Run and manually review all six cases in `evaluation/demo_v1.json`, including
      both qualitative facts. Validate an additional non-preset interactive question.
- [x] Capture real demonstration images and a short GIF or recording (saved-result
      walkthrough, explicitly not a live-generation recording).
- [x] Finish Windows setup, architecture explanation, limitations, readable README,
      actual-results-based resume bullets and interview notes.
- [x] Run tests/lint, verify documentation links and review the publishable file set.
- [x] Publish the repository contents and verify the actual GitHub-rendered materials.

## Data Selection Policy (Before New Experiments)

Keep the already-exposed 3M 2018 report in development. Add PepsiCo 2022 to development
because it has the highest count of extraction-only questions among the cached
FinanceBench 2022 annual reports. Reserve AMD 2022 and CVS Health 2022 for final
evaluation: non-bank 2022 annual reports with two extraction-only public questions,
selected alphabetically among that group. American Express is excluded from this
numeric-table prototype's non-bank scope; Ulta's report is a different year.

Use original extraction questions where compatible with supported numeric output;
fill missing coverage with predefined numeric categories (revenue, net income,
total assets, capex, net PP&E, operating cash flow). Record substitutions and labels
before running the new evaluation. Do not select on model success. Original developer
questions remain exposed. Inspect source tables for annotation, but never use final
answers to tune the pipeline. If final results lead to code changes, mark them as
exploratory and do not claim they remain held out.

## Completed Local Acceptance

The 2026-09-19 GPU session completed numeric development checks, both
retrieval/generation methods on the frozen final split, all six demonstrations,
a new browser question and an isolated reproduction. Source review and actual
failure records are in [SOURCE_REVIEW.md](SOURCE_REVIEW.md) and
[FAILURE_ANALYSIS.md](FAILURE_ANALYSIS.md). Final numeric target matches are 5/12
dense and 9/12 hybrid; requiring direct citation support gives 5/12 and 8/12.
Do not collapse these into one accuracy claim. All three final refusal probes
pass per method, including two programmatic scope checks.

The six-case demonstration is accepted after one fact-prompt correction; the
failed earlier quote is retained. The fresh-index reproduction reused downloaded
assets and the existing Ollama runtime, not a clean-machine install. 127 CPU tests
and Ruff pass. The model was unloaded and the project-owned service stopped;
the remaining local viewer does not use GPU. See [ACCEPTANCE_AUDIT.md](ACCEPTANCE_AUDIT.md).

The local research prototype is ready to be described using [RESUME.md](RESUME.md).
Repository publication and GitHub rendering were verified on 2026-09-19 for
commit `4b22b78`; see [ACCEPTANCE_AUDIT.md](ACCEPTANCE_AUDIT.md).

## Earlier Progress Record

The following records the state before the final GPU session, not current blockers.

Statement-first selection included the target chunk but produced only 7/9 on the
exposed development set; distracting non-requested statements still won citations.
The statement-filtered variant is implemented; GPU validation is pending
coordination. A schema fix removes duplicate required-field entries without
changing numeric expectations. Historical artifacts remain unchanged.

Four complete reports have been indexed on CPU (997 pages, 2,245 chunks). The
30-case question set is annotated and document-separated; the model configuration
has not yet been frozen. CPU development retrieval is complete: dense 9/12 and
hybrid 10/12 gold-page Recall@10, with weaker hybrid Recall@5 retained in the report.
The local evidence workspace defaults to GPU disabled, supports saved real outputs
and CPU-rendered original pages. Current generation results, final semantic review,
live GPU interaction and final resume claims remain pending.

CPU-side verification now passes 121 tests and Ruff, with local documentation-link
checks included. Desktop/mobile screenshots and a labeled saved-result GIF are
available in `docs/images/`; see `docs/UI_VALIDATION.md`. Windows setup, architecture,
limitations and a Chinese interview/learning outline have been updated. No commit
or push has been made. The next substantive acceptance step requires an explicitly
confirmed GPU session for development generation, then configuration freezing and
final evaluation.

Acceptance review restored the missing qualitative demonstration requirement.
An explicit report-fact mode now uses the same retrieval/source checks and delivers
a short original excerpt rather than unverified paraphrase. It is CPU-tested but
not yet model-validated. Numeric evaluation questions remain unchanged. The freeze
also covers `rag_check.py`, which owns numeric scoring. The six-case demonstration
manifest is development-only and does not replace the final evaluation.

The report-fact CPU experiment preserves its initial risk-context miss and its
branch-coverage follow-up in `artifacts/demo/`. Both hybrid fact examples now have
their annotated page in context; dense still misses one. This is not answer accuracy.
The numeric development regression retains all 30 earlier retrieval metrics and
supplied chunk lists. See `docs/ACCEPTANCE_AUDIT.md` for remaining evidence gaps.
