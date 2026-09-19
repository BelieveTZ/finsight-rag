# Acceptance Evidence Audit

Date: 2026-09-19. **Local portfolio scope accepted; repository presentation verified.**
This is a reproducible, honestly describable financial RAG research prototype,
not a production assistant. The specification's four-document/two-retriever
reductions are applied; all six real demonstration cases are retained.

| Requirement | Evidence currently available | Still needed |
| --- | --- | --- |
| Full, traceable corpus | Four pinned reports; 997 pages, 2,245 chunks; full-PDF audits and blank-page review | No OCR; fixed corpus only |
| Dense/hybrid comparison | Complete development and frozen final generation; per-case outputs retained | Small, non-independent authored set |
| Development/final separation | 24 numeric + 6 refusal questions; document-disjoint splits; frozen config verified | Do not tune on the final results and retain the same claim |
| Citation/refusal behavior | Every current delivered answer reviewed against sources; direct support separated from numeric match | Semantic errors still pass guards; ambiguous target definition recorded |
| Six demonstrations | Two numeric, two facts, two refusals; 6/6 accepted, 4/4 answered citations supported | Development demonstrations, not general accuracy |
| Non-preset interaction | New live cash-balance question correct; real connection failure shown separately; unload verified | In-app browser checked, no cross-browser certification |
| Metrics and failures | Final target matches 5/12 vs 9/12; directly supported target matches 5/12 vs 8/12; timing/VRAM/cost and failures recorded | No production or generalization claim |
| Reproducibility | Isolated source export, new locked environment, fresh index and genuine local generation | Reused downloaded assets/runtime; not a clean-machine network install or remote clone |
| Repository presentation | Published README, rendered results table, loaded evidence screenshot, animated GIF and Chinese/English resume document checked on GitHub | No hosted application; local setup required for new questions |
| Tests and review | 127 CPU tests and Ruff; local documentation links; desktop/mobile screenshots | Tests do not replace the separate actual model evidence |

## Publication Boundary

The GPU session has finished. The model was unloaded and the verified
project-owned Ollama process stopped. Only a CPU-only local viewer remains.
Confirm that other training has stopped before a future GPU session.

Local evidence is sufficient to describe the project as the scoped research
prototype in [RESUME.md](RESUME.md). It is not a claim that the larger unabridged
specification or production quality has been achieved. The implementation and
evidence were published to the existing repository's `main` branch in commit
[`4b22b78`](https://github.com/BelieveTZ/finsight-rag/commit/4b22b786e009eeda38243a18058433119a8285fb).
The GitHub README results table, evidence image, linked animated walkthrough and
Chinese/English resume document were checked in the browser on 2026-09-19.
Local Markdown links pass the automated path check. This is repository publication,
not an online application deployment or a clean-machine reproduction claim.

Publication verification is recorded separately from local acceptance. See
[reproduction](REPRODUCTION.md), [source review](SOURCE_REVIEW.md) and
[evaluation](PORTFOLIO_EVALUATION.md) for the evidence and its limits.
