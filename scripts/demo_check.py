"""Record six exposed demonstrations; semantic review remains a separate step."""

import argparse
import json
import time
from datetime import UTC, datetime

from pypdf import PdfReader

from scripts.corpus import ROOT, document, pdf_path
from scripts.local_smoke import MODEL, GpuMonitor, api
from scripts.portfolio_eval import configuration
from scripts.rag import answer_question
from scripts.rag_check import score
from scripts.retrieval import sha256
from scripts.retrieval_check import build_index

MANIFEST = ROOT / "evaluation/demo_v1.json"


def automatic_check(row, case):
    """A source-valid fact still needs a person to check relevance and completeness."""
    if not row.get("structurally_valid"):
        return False
    answer = row.get("answer", {})
    if answer.get("status") != case["expected_status"]:
        return False
    if case["expected_status"] == "insufficient_evidence":
        return True
    if case["answer_kind"] == "numeric":
        return score(answer, case)
    return answer.get("pdf_page") in case["evidence_pages"]


def evaluate(allow_gpu=False):
    if not allow_gpu:
        raise ValueError("Coordinate GPU availability, then pass --allow-gpu")
    cases = json.loads(MANIFEST.read_text(encoding="utf-8"))["cases"]
    if any(document(c["document_id"])["split"] != "development" for c in cases):
        raise ValueError("Demonstrations must not tune on final documents")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    public = ROOT / "artifacts/demo" / f"{stamp}-generation.json"
    private = ROOT / ".cache/demo" / public.name
    for path in (public, private):
        path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "at_utc": stamp,
        "scope": "Six exposed demonstrations, not held-out accuracy",
        "manifest_sha256": sha256(MANIFEST),
        "config": configuration(),
        "runner_sha256": sha256(ROOT / "scripts/demo_check.py"),
        "api_cost_usd": 0,
        "semantic_review": "pending; automatic checks do not establish semantic correctness",
        "expected_records": len(cases),
        "completed": False,
        "indexes": {},
        "results": [],
    }

    def save():
        private.write_text(json.dumps(report, indent=2), encoding="utf-8")
        summary = {**report, "private_trace_sha256": sha256(private)}
        summary["results"] = [
            {k: v for k, v in row.items() if k not in ("messages", "raw_response", "gpu_samples")}
            for row in report["results"]
        ]
        public.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    try:
        report["ollama_version"] = api("/api/version")
        report["installed_models"] = api("/api/tags")
        for doc_id in dict.fromkeys(c["document_id"] for c in cases):
            print(f"Preparing {doc_id} (CPU)", flush=True)
            retriever, tokenizer, setup = build_index("table-v1", doc_id)
            report["indexes"][doc_id] = setup
            reader = PdfReader(pdf_path(doc_id))
            for case in (c for c in cases if c["document_id"] == doc_id):
                row = {"case_id": case["id"], "document_id": doc_id}
                start = time.perf_counter()
                monitor = GpuMonitor()
                try:
                    with monitor:
                        row.update(
                            answer_question(
                                case["question"],
                                retriever,
                                tokenizer,
                                reader,
                                document=document(doc_id),
                                answer_kind=case["answer_kind"],
                            )
                        )
                    row["automatic_check_passed"] = automatic_check(row, case)
                except Exception as error:
                    row.update(error=str(error), automatic_check_passed=False)
                finally:
                    row["wall_seconds"] = time.perf_counter() - start
                    row["gpu_samples"] = monitor.samples
                    row["gpu_sampling_errors"] = monitor.errors
                    row["device_peak_used_mib"] = max(
                        (g["used_mib"] for s in monitor.samples for g in s["gpus"]), default=None
                    )
                report["results"].append(row)
                save()
                print(case["id"], row["automatic_check_passed"], row.get("answer"), flush=True)
    except KeyboardInterrupt:
        report["run_error"] = "Interrupted before completion"
    except Exception as error:
        report["run_error"] = str(error)
    finally:
        try:
            api("/api/generate", {"model": MODEL, "keep_alive": 0})
            report["after_unload"] = api("/api/ps")
            if any(m.get("name") == MODEL for m in report["after_unload"].get("models", [])):
                raise RuntimeError("Model still loaded")
        except Exception as error:
            report["unload_error"] = str(error)
        report["completed"] = len(report["results"]) == len(cases) and "run_error" not in report
        save()
    print(f"Report: {public}", flush=True)
    return int(
        not report["completed"]
        or "unload_error" in report
        or any(not r["automatic_check_passed"] for r in report["results"])
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-gpu", action="store_true")
    raise SystemExit(evaluate(parser.parse_args().allow_gpu))
