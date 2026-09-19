# Reproduction Record

Date: 2026-09-19. An isolated current-source export was tested under
`.cache/rehearsal-20260919`, without copying the working virtual environment or
retrieval vector cache. This was **not** a fresh remote clone or a clean-machine
network-install test. The project had not been committed/pushed during this check.

## What Was Recreated

- A new Python 3.12.14 virtual environment, synchronized against `uv.lock`.
- Locked dependencies from the existing local package cache. The PDFium wheel
  required a separate local-wheel install because the registry cache was incomplete;
  its previously verified SHA-256 is
  `47dcca2a8d507b5fd24f94c3c9d48fb379430f097bc20f01beff6c963ffbcedb`.
- Copies of the pinned PDFs and CPU embedding assets, with no vector cache.
- The frozen retrieval/generation source and corpus registry.
- 127 CPU tests, plus Ruff with its cache disabled.

One end-to-end command was run from the isolated export:

```powershell
.\.venv\Scripts\python.exe -m scripts.rag_check --document 3M_2018_10K --question "What were 3M's FY2018 capital expenditures in USD millions?"
```

The [actual report](../artifacts/reproduction/20260919T070819851804Z.json) records:
431 chunks; `vector_cache_hit=false`; 85.78 s index setup including 35.41 s vector
construction; 58.82 s question wall time from an unloaded model; correct answer
1,577 USD millions from PDF page 46; all source/unit checks passed. The model was
confirmed unloaded afterward. This reuses the project's already-installed local
Ollama runtime/model, not a newly downloaded 5 GB model. No paid endpoint was used.

## Windows Findings

Initial isolated tests encountered file permissions on the shared Windows temporary
directory, not assertion failures in the application. Running with a new
project-local `--basetemp` and without the pytest cache completed 127 tests in 3.93 s.
The workaround and safe new-directory requirement are in [Windows setup](LOCAL_SETUP.md).
The first restricted test process was interrupted during teardown; it is not counted
as a successful completed run.

`.gitattributes` fixes LF line endings for source/data/lockfiles, preserving frozen
byte hashes after Windows checkout. Binary screenshots/GIFs are excluded from text
conversion. The final pipeline still matches `evaluation/portfolio_config.json`.

## Limits

This demonstrates a new environment and a fresh index for one development document,
not a second full final-set run, independent evaluation, or a no-cache internet
installation. Dependencies and asset downloads remain prerequisites for another
machine. Do not run the CLI and GPU-enabled web app concurrently: they share one
dedicated model service and each owns its cleanup. The default viewer uses no GPU.
