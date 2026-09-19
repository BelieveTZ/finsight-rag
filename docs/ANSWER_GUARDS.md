# Answer Validation Follow-Up

Date: 2026-09-19. Scope: make the existing single-report prototype fail closed on
observed errors, not claim general financial QA reliability.

## Changes

- Before retrieval/generation, require an explicit 3M reference and one year from
  2016-2018. Reject recognized comparative phrasing and conflicting possessive
  company references. Unsupported inputs receive a nonempty explanation and no
  invented number or citation. This is a deliberately narrow supported scope,
  not a claim that other data cannot exist in the annual report.
- Require a nonempty explanation in the generation schema, and independently
  validate it. An invalid generated response is preserved as `model_answer` but
  delivered as an explicit validation refusal in `answer`.
- Check that the quote contains a number consistent with the declared millions /
  billions unit. Source units must be explicit in the quote or a recognized
  millions header; unknown units fail closed. For example, 8,738 million cannot
  support an output value of 8738 with unit `USD billions`.
- Check requested output units, year presence, document ID and explicit balance
  sheet / cash-flow statement constraints. Cash-flow title matching tolerates
  PDF whitespace splitting, including the actual extracted `Cash Flow s`.
- Render accepted answer prose from the checked numeric fields, year and citation
  so prose cannot independently claim 8.738 billion while the field says 8738.
  The model's original prose remains available for inspection.

The PDF, retrieval settings, query processing, context-prefix policy and nine-case
evaluation manifest are unchanged. There are no expected answers in the guards.
No paid API, new model, model training or new dependency was used.

## Regression Evidence

Six targeted tests first failed on the original implementation: unsupported scope
reached retrieval, the schema permitted an empty explanation, and unit consistency
was not checked. Additional tests cover new company/year variants, ambiguous
company ownership, explicit billion-to-million conversion, unknown units and
statement constraints. All 68 unit tests now pass.

The first real guarded run is retained:
[20260919T050840659371Z](../artifacts/rag/20260919T050840659371Z.json).
It passed 7/9 cases, but introduced a capex false refusal because PDF extraction
split `Flows` into `Flow s`. A failing regression test reproduced this exact title,
then whitespace-tolerant matching fixed it. The PPNE error was blocked rather
than turned into a fabricated correct answer. The three unsupported-scope cases
were refused by application rules without calling the generator.

Final rerun:
[20260919T051129788925Z](../artifacts/rag/20260919T051129788925Z.json).
It passed **8/9**: five of six numeric questions and all three application-scope
refusals. PPNE remains a failed task, now with a validation refusal instead of an
incorrect delivered number. The nine-case manifest hash matches the original run;
no expected answers were changed. This is an application-level development result,
not 8/9 raw model accuracy or an independent benchmark.

Cached-index setup took 46.65 seconds. The first generated answer took 52.72 seconds
including model loading; the other five generated cases took 4.44-8.63 seconds
(median 4.96). Scope refusals took about 0.04 seconds after shared setup. Sampled
whole-device VRAM peaked at 8,867 MiB (8.66 GiB), including unrelated GPU use.
Do not compare these timings as a controlled speed benchmark against September 16.
The final model-list check was empty. The dedicated server started for this test
was also stopped after verifying its recorded executable, PID and start time.

## Interpretation and Limits

`generation_skipped`, `decision`, `model_answer`, validation flags and supplied
chunk IDs distinguish application scope refusals, generated answers and validation
refusals. An answerable question that is refused still fails task completion;
guardrails do not convert that into a success. `structurally_valid` remains the
legacy overall raw-response check flag, not a guarantee of semantic correctness.

Company detection is a narrow English heuristic, not named-entity recognition.
Merely mentioning 3M can still leave a more complex question ambiguous. Year
presence is not year-to-column alignment. Numeric matching tests magnitude and
unit consistency, not sign correctness or whether the matched number belongs to
the requested metric/year. Statement detection only recognizes specific headings.
Unknown phrasing can be rejected unnecessarily, and unsupported semantics can
escape these checks. No general safety, factual-accuracy or adversarial-robustness
claim is made.

The conservative context budget still omits the balance-sheet PPNE chunk at rank
ten. Fixing evidence selection is the next bounded step; do not silently fill in
that answer from an evaluation label. Independent documents/questions and in-scope
unanswerable questions are still needed before acceptance. Passing out-of-scope
cases now measures deterministic application refusal, not improved model refusal.

## Windows Reproduction

Use the existing setup in [LOCAL_SETUP.md](LOCAL_SETUP.md). Start the dedicated
local service if needed, then run from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.rag_check
.\.venv\Scripts\python.exe -m scripts.rag_check --question "What was Microsoft's FY2018 revenue?"
```

The evaluation returns a nonzero exit code while any required answer fails. Public
reports remain in `artifacts/rag/`; full evidence/raw responses remain in ignored
`.cache/rag/`. The runner unloads model weights in its cleanup path.
