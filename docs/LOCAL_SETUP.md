# Windows Local Setup

## Current Evidence Workspace

From the repository root, start the default **CPU-only saved-result viewer**:

```powershell
.\.venv\Scripts\python.exe -m scripts.app --port 8765
```

Open `http://127.0.0.1:8765`. This displays real saved development answers,
checks, retrieved chunk IDs and CPU-rendered original report pages. Saved outputs
are labeled and do not represent a new model run. The question button is disabled
until inference is explicitly enabled. If the port is occupied, choose another
port; do not stop an unknown process.

For a fresh clone, first install the locked Python environment using the setup
below. Then prepare the small embedding model and pinned reports on CPU:

```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_retrieval
.\.venv\Scripts\python.exe -m scripts.prepare_corpus --download
```

Downloads need internet; later indexing, previews and inference use local files.
Full-PDF preparation can take several minutes. The corpus consists of 997 pages,
including report exhibits, not only the labeled evidence pages. Missing PDFs show
a preview error; no replacement document is silently downloaded by the web app.

**Coordinate GPU use first.** Another project's training may be using VRAM. Wait
until it has stopped before enabling inference. No automatic process termination
or game-detection service is installed. In separate terminals:

```powershell
# Dedicated local model service, after the GPU is available.
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_ollama.ps1

# Stop the CPU-only web server with Ctrl+C first, or choose an unused port.
.\.venv\Scripts\python.exe -m scripts.app --port 8765 --allow-gpu
```

The model must have been pulled once, as described below. Live questions use the
16,384-token RAG context; earlier development runs sampled close to 9 GiB of
whole-device memory. This is not a guaranteed per-process VRAM budget. First
questions also prepare the selected document's CPU index. The web app unloads the
model after each question and reports cleanup failures. CPU indexes stay in RAM
until the server is stopped. Use Ctrl+C to stop the web server; avoid interrupting
an active question before cleanup finishes. Do not expose either port externally.

Read [architecture](ARCHITECTURE.md) for what each step does, and
[evaluation](PORTFOLIO_EVALUATION.md) for the development/final commands.
The workspace has separate Numeric and Report fact modes. Fact mode displays an
original excerpt and supports the selected report year only; the two fixed fact
demonstrations passed source review. The [six-case demo protocol](FACT_DEMO.md) explains its limits
and reproduction commands. Never treat a source-string match as proof of relevance.

## Earlier Supplied-Evidence Check

The newer [end-to-end local QA prototype](RAG_SMOKE.md) connects actual retrieved
evidence to Qwen and documents its known failures. It uses a 16,384-token context
with a higher GPU memory footprint. The original 4,096-token smoke test below
remains a separate supplied-evidence check.

This is a supplied-evidence generation check, not the complete RAG application.
For the subsequently added CPU full-report retrieval experiment, see
[retrieval setup and results](RETRIEVAL_CHECK.md). The commands below describe the
generation smoke test; its runtime needs only the Python standard library, whereas
the repository's current lockfile also includes the retrieval dependencies.
No paid API, account token, web deployment, PyTorch, or CUDA Toolkit is required.
Ollama supplies the inference runtime; Python uses the standard library to call it.

## Prepared Machine

Run these commands from the repository root in PowerShell. The prepared environment
uses Python 3.12.14, uv 0.12.15 and Ollama 0.34.1. It does not change the system PATH
or require activating a virtual environment.

```powershell
# Start the dedicated local service; do not start a second copy.
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_ollama.ps1
Invoke-RestMethod http://127.0.0.1:11435/api/version

# Run the real model checks: six questions, three repetitions.
.\.venv\Scripts\python.exe scripts/local_smoke.py

# Test the validation logic without loading the model.
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check scripts tests
```

The execution-policy option applies only to that PowerShell process, not globally.
If port 11435 is occupied, inspect the existing service; do not kill an unknown process.
The service binds only to `127.0.0.1:11435`, disables Ollama cloud features, allows
one loaded model and one request at a time, and defaults to 4096 context tokens.
Startup logs are in `.runtime/ollama.stderr.log` and `.runtime/ollama.stdout.log`.

The smoke script uses the fixed loopback address directly, ignoring HTTP proxies.
There is no automatic remote fallback. It unloads model weights when finished;
the lightweight local server may remain running for the next session.

## Fresh Clone

Prerequisites: Windows, a supported NVIDIA driver, `nvidia-smi`, and
[uv](https://docs.astral.sh/uv/getting-started/installation/). This machine uses
an RTX 4070 SUPER with 12 GB VRAM. Close other GPU-heavy workloads first.
Allow disk headroom for the compressed runtime, extracted libraries, Python and
approximately 5.2 GB of model downloads. Downloads need internet access; inference
does not, once all assets are present.

```powershell
New-Item -ItemType Directory -Force .tools, .cache | Out-Null
# Keep managed Python and caches in the project drive.
$env:UV_PYTHON_INSTALL_DIR = Join-Path $PWD '.tools\python'
$env:UV_CACHE_DIR = Join-Path $PWD '.cache\uv'
uv python install 3.12.14 --no-bin --no-registry
uv sync --locked

curl.exe --fail --location --retry 3 --output .tools/ollama-windows-amd64.zip https://github.com/ollama/ollama/releases/download/v0.34.1/ollama-windows-amd64.zip
$expected = '428c94622a04764b318ddf13a061898edf69e32ffa896f638ed6015fd3f33288'
if ((Get-FileHash .tools/ollama-windows-amd64.zip -Algorithm SHA256).Hash -ne $expected) {
    throw 'Ollama archive checksum mismatch; do not extract or run it.'
}
Expand-Archive -LiteralPath .tools/ollama-windows-amd64.zip -DestinationPath .tools/ollama
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_ollama.ps1
Invoke-RestMethod http://127.0.0.1:11435/api/version

$env:OLLAMA_HOST = '127.0.0.1:11435'
.\.tools\ollama\ollama.exe pull qwen3:8b-q4_K_M

# Verify the recorded model identity; a mutable tag alone is not a weight pin.
$model = (Invoke-RestMethod http://127.0.0.1:11435/api/tags).models |
    Where-Object { $_.name -eq 'qwen3:8b-q4_K_M' }
if ($model.digest -ne '500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41') {
    throw 'Model digest differs from the recorded evaluation; inspect before comparing results.'
}

curl.exe --fail --location --retry 3 --output .cache/financebench_open_source.jsonl https://raw.githubusercontent.com/patronus-ai/financebench/main/data/financebench_open_source.jsonl
.\.venv\Scripts\python.exe scripts/local_smoke.py
```

On the already prepared machine, the uv executable is
`.tools/bootstrap/Scripts/uv.exe`; substitute that path for `uv` when needed.
Its bootstrap used the desktop application's bundled Python, but `.venv` uses the
independently downloaded Python under `.tools/python` and does not depend on that
bundled interpreter for normal operation. Managed Python builds are distributed
by Astral; see [uv Python installation](https://docs.astral.sh/uv/guides/install-python/).

The FinanceBench file is pinned by SHA-256 in the smoke script. If upstream changes,
the script stops: inspect the change instead of silently accepting a different test.
The exact input page is identified in each result file. The source PDF has not been
independently inspected in this smoke test; page numbering comes from FinanceBench.

## What Is Checked

- Three answerable cases: 3M capital expenditures in 2018 and 2017, and dividends
  in 2018, with amounts in USD millions, document ID, PDF page and verbatim quote.
- Three refusal cases: missing year, missing metric, and pressure to guess.
- JSON structure, correct numeric fields, units, citation metadata, quote presence
  in the supplied evidence, and non-truncated output.
- Each case repeats three times at temperature 0 and seed 42. Repetitions are
  stability checks, not additional independent evaluation questions.

Results under `artifacts/local-smoke/` include raw answers, prompts, model metadata,
source hashes, per-request timing and GPU samples. A nonzero exit code means a run
or answer check failed; retain failed reports as well as successful ones.
Automated quote matching does not prove semantic support; inspect the actual answers.
Generation uses separate JSON-schema branches for answered and refused responses.
This enforces null citation fields on refusal; the checker still independently
verifies status, value and citation correctness. See the [measured results](LOCAL_VALIDATION.md)
for the initial failure and the subsequent constrained-generation run.

The first request loads an unloaded model; subsequent requests reuse loaded weights
and may benefit from prompt caching. This is not a cold operating-system/disk-cache
test. Wall time includes the complete non-streamed response, not first-token latency.
`nvidia-smi` samples approximately every 0.2 seconds plus command overhead: sampled
peaks can miss shorter spikes and include desktop/other GPU processes. Ollama's
`size_vram` is reported separately and is not interchangeable with whole-device usage.

Reserve this page and these questions for development/demo use. Do not count them
as held-out FinanceBench evaluation or claim retrieval accuracy from this run.
Embedding and PDF extraction are now available in the separate retrieval experiment.
Reranking remains deferred. The newer evidence workspace is described above.

## Troubleshooting

- Connection refused: start the local service, wait for readiness, inspect its logs.
- Model not found: use the exact pull tag above with `OLLAMA_HOST` set to port 11435.
- Out of memory: close other GPU workloads and retry the fixed 4096-token setting;
  do not silently switch models or use a paid endpoint.
- Slow responses: inspect `.tools/ollama/ollama.exe ps` with the host configured;
  CPU offloading and other GPU workloads may affect performance.
- First live question: allow time for full-report extraction and model loading;
  the measured first browser question took about two minutes. The app unloads after
  each question, so batch warm latency is not an interactive startup estimate.
- Evaluation freeze already exists in a clone: do not repeat `--freeze` or overwrite
  it. Run the final command directly against unchanged source. Future experiments
  need a new labeled version; final-driven revisions are not held-out results.
- Broken environment: rerun `uv sync --locked`; do not copy an old virtual environment.
- Windows temporary-directory permission errors in tests: use a new project-local
  temporary directory instead of changing permissions on the user's shared temp tree:

  ```powershell
  $testTemp = Join-Path $PWD ('.cache\pytest-' + [guid]::NewGuid().ToString('N'))
  .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=$testTemp
  .\.venv\Scripts\python.exe -m ruff check --no-cache scripts tests
  ```

  Use a new path each time: pytest clears an explicitly supplied existing base
  directory. Do not point it at the project root or any folder containing work.
- Server cleanup: close only the process recorded in `.runtime/ollama-process.json`
  after verifying its executable and start time, or let Windows stop it at shutdown.

Runtime references: [Ollama Windows](https://docs.ollama.com/windows),
[local-only mode](https://docs.ollama.com/faq),
[chat API and timing fields](https://docs.ollama.com/api/chat),
[loaded-model VRAM](https://docs.ollama.com/api/ps).
