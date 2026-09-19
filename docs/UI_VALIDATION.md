# Local Workspace Verification

## Current Acceptance

On 2026-09-19, the local GPU session verified a new browser question,
not present in the saved demonstrations: 3M cash and cash equivalents at year-end
2018. The actual answer was 2,853 USD millions from PDF 60, with a matching source
quote and chunk ID. Original page inspection confirmed the row and year.

- The UI showed index preparation, then retrieval/generation; controls were disabled
  while running, and the previous answer/citation was cleared.
- It displayed a **Live result**, re-enabled controls and loaded the actual source
  image. Full first-request time was 120.85 s, including CPU setup and model startup.
- `/api/ps` was empty after completion. The task-owned model service was then stopped.
- A request against that stopped service displayed **Request failed**, not a refusal
  or success; no answer citation or stale metrics remained. Cleanup failure was visible.
- The GPU-enabled temporary web server was stopped after this check. The default
  CPU-only viewer remains the normal startup path.

Current screenshots: [live question](images/live-cash-question.png),
[real service failure](images/live-service-error.png),
[accepted business fact](images/accepted-fact-desktop.png), and
[mobile layout](images/accepted-fact-mobile.png). Desktop 1366 x 900 and mobile
390 x 844 checks showed no horizontal overflow; original source images loaded at
1,600-pixel maximum dimension. Screenshots were visually inspected.

The saved menu now contains all six rows of the source-reviewed run
`20260919T065722467425Z-generation.json`. Selecting a fact restores Report fact mode;
selecting a numeric example restores Numeric mode. The raw `insufficient_evidence`
answer string is displayed as a readable evidence-insufficiency message; original
artifacts are unchanged. This presentation change does not change model decisions.

[The current GIF](images/accepted-workspace.gif) combines three real saved-result
screenshots, four seconds each. It is not a live generation recording. Rebuild it
with `python -m scripts.build_demo_gif`. Current verification: 127 tests, Ruff and
local documentation-link checks pass. No cross-browser certification is claimed.

## Earlier CPU-Only Check

Checked earlier on 2026-09-19, with GPU inference disabled throughout. No new model result
was produced by this browser verification. Saved answers come from the real prior
development run `20260919T051129788925Z.json`.

Verification: 121 tests passed, Ruff passed, local Markdown links resolved, and
the locked environment synchronized successfully offline after installing the
checksum-verified PDFium wheel. The interface was checked in the in-app browser;
cross-browser live-inference acceptance is still pending.

The subsequent report-fact controls were checked at the same desktop/mobile
dimensions and screenshots recaptured. Changing modes clears saved output and
keeps the GPU-disabled question button disabled. Loading a saved numeric run
restores Numeric mode. The supplied PDF preview is not a fact-model result.

## Observed Checks

- Desktop 1366 x 900 and mobile 390 x 844: no horizontal document overflow;
  source images load at 1,600-pixel maximum dimension. Full-page screenshots inspected.
- Saved capex: answer 1,577 USD millions, source quote, chunk ID and original PDF
  page 60 agree. Expanding checks exposes the stored pass/fail outcomes.
- Page stepper, explicit page entry with Enter and retrieved-evidence links change
  the preview. Browsing another page does not rewrite the answer's citation link.
- Saved FY2024 question against the 2018 report: scope refusal, zero model evidence,
  no citation; UI explicitly says the model was not called.
- Changing to AMD clears the previous answer and switches document metadata;
  PDF page 54 can be selected without starting generation.
- The default question button is disabled. HTTP tests reject inference without
  opt-in, cross-origin submissions, unknown routes and path traversal.

The original embedded PDF viewer was blank in the in-app browser. The current
implementation renders original PDF pages on CPU and retains a full-PDF link.
It does not require an external PDF plug-in or GPU. Missing files have a visible
preview error. Renderer tests cover PNG output and out-of-range page rejection.

## Demonstration Assets

- `images/saved-capex-desktop.png`: saved answer and original source page.
- `images/saved-capex-mobile.png`: responsive layout.
- `images/saved-capex-checks.png`: expanded stored validation checks.
- `images/saved-scope-refusal.png`: explicit rule-based refusal.
- `images/saved-workspace.gif`: three real screenshots in sequence, four seconds
  each. It is a saved-result walkthrough, **not a real-time generation recording**.

The screenshots contain original report pages for evidence inspection. They are
not an endorsement by the issuers. Full reports remain local and ignored.

The original GIF is retained as historical evidence. The builder now rebuilds the
accepted-result GIF from current screenshots:

```powershell
.\.venv\Scripts\python.exe -m scripts.build_demo_gif
```

The formerly pending live question, waiting/error/cleanup behavior and final QA
checks were completed in the current acceptance section above. Unit tests alone
did not replace these real end-to-end checks.
