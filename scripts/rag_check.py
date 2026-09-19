"""Run the local RAG candidate on a question or the frozen development smoke set."""

import argparse
import json
import math
import time
from datetime import UTC, datetime

from pypdf import PdfReader

from scripts.corpus import document, pdf_path
from scripts.local_smoke import MODEL, GpuMonitor, api
from scripts.rag import OPTIONS, answer_profile, answer_question
from scripts.retrieval import sha256
from scripts.retrieval_check import ROOT, build_index


def score(answer, case):
    if not isinstance(answer, dict):
        return False
    if case["value"] is None:
        return answer.get("status") == "insufficient_evidence"
    value = answer.get("value")
    return (
        answer.get("status") == "answered"
        and type(value) in (int, float)
        and math.isfinite(value)
        and math.isclose(value, case["value"], rel_tol=0, abs_tol=0.0001)
        and answer.get("unit") == case["unit"]
    )


def main(question=None, context_mode="statement-filtered", document_id=None, answer_kind="numeric"):
    system, schema = answer_profile(answer_kind)
    if not question and (document_id is not None or answer_kind != "numeric"):
        raise ValueError("Choose --question when selecting a document or report-fact mode")
    selected_document = document(document_id) if document_id else None
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    private = ROOT / ".cache/rag" / (stamp + ".json")
    public = ROOT / "artifacts/rag" / (stamp + ".json")
    for path in (private, public):
        path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "scope": "development end-to-end smoke, not held-out accuracy",
        "model": MODEL,
        "options": OPTIONS,
        "system": system,
        "schema": schema,
        "answer_kind": answer_kind,
        "document": selected_document,
        "query_mode": "financial-v1",
        "context_mode": context_mode,
        "results": [],
        "implementation_sha256": {
            name: sha256(ROOT / "scripts" / name)
            for name in (
                "rag.py",
                "rag_check.py",
                "retrieval.py",
                "query_processing.py",
                "answer_guards.py",
            )
        },
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
        retriever, tokenizer, report["retrieval_setup"] = (
            build_index("table-v1", document_id) if document_id else build_index("table-v1")
        )
        reader = PdfReader(
            pdf_path(document_id) if document_id else ROOT / ".cache/3M_2018_10K.pdf"
        )
        manifest = ROOT / "evaluation/rag_dev_v1.json"
        cases = (
            [{"id": "interactive", "question": question}]
            if question
            else json.loads(manifest.read_text(encoding="utf-8"))["cases"]
        )
        report["evaluation_manifest_sha256"] = None if question else sha256(manifest)
        for case in cases:
            started = time.perf_counter()
            row = {"case_id": case["id"]}
            with GpuMonitor() as monitor:
                try:
                    row.update(
                        answer_question(
                            case["question"],
                            retriever,
                            tokenizer,
                            reader,
                            context_mode,
                            document=selected_document,
                            answer_kind=answer_kind,
                        )
                    )
                    if not question:
                        row["expected_value_and_unit_or_refusal"] = score(row["answer"], case)
                        row["passed"] = (
                            row["structurally_valid"] and row["expected_value_and_unit_or_refusal"]
                        )
                except Exception as error:
                    row.update(error=str(error), passed=False)
            row["wall_seconds"] = time.perf_counter() - started
            row["gpu_samples"] = monitor.samples
            row["gpu_sampling_errors"] = monitor.errors
            used = [g["used_mib"] for s in monitor.samples for g in s["gpus"]]
            row["peak_device_used_mib"] = max(used, default=None)
            report["results"].append(row)
            save()
            print(
                json.dumps(
                    {
                        k: v
                        for k, v in row.items()
                        if k in ("case_id", "answer", "checks", "passed", "wall_seconds", "error")
                    }
                ),
                flush=True,
            )
    except Exception as error:
        report["run_error"] = str(error)
    finally:
        try:
            api("/api/generate", {"model": MODEL, "keep_alive": 0})
            report["after_unload"] = api("/api/ps")
            if any(m.get("name") == MODEL for m in report["after_unload"].get("models", [])):
                report["unload_error"] = "Model still loaded"
        except Exception as error:
            report["unload_error"] = str(error)
        save()
    print(f"Report: {public}", flush=True)
    return int(
        "run_error" in report
        or "unload_error" in report
        or not report["results"]
        or any(not r.get("passed", r.get("structurally_valid", False)) for r in report["results"])
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question")
    parser.add_argument(
        "--document", help="Whitelisted corpus document ID for an interactive question"
    )
    parser.add_argument("--answer-kind", choices=("numeric", "fact"), default="numeric")
    parser.add_argument(
        "--context-mode",
        choices=("ranked-prefix", "statement-first", "statement-filtered"),
        default="statement-filtered",
    )
    args = parser.parse_args()
    raise SystemExit(main(args.question, args.context_mode, args.document, args.answer_kind))
