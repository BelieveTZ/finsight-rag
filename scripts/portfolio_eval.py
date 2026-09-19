"""Document-separated portfolio evaluation. GPU generation requires an explicit opt-in."""

import argparse
import json
import time
from dataclasses import asdict
from datetime import UTC, datetime

import numpy as np
from pypdf import PdfReader

from scripts.corpus import CATALOG, ROOT, document, pdf_path
from scripts.local_smoke import MODEL, GpuMonitor, api
from scripts.query_processing import prepare_query
from scripts.rag import ANSWER_SCHEMA, OPTIONS, SYSTEM, answer_question, select_context
from scripts.rag_check import score
from scripts.retrieval import normalize, page_metrics, sha256
from scripts.retrieval_check import build_index

MANIFEST = ROOT / "evaluation/portfolio_v1.json"
FREEZE = ROOT / "evaluation/portfolio_config.json"


def configuration():
    names = (
        "rag.py",
        "rag_check.py",
        "answer_guards.py",
        "query_processing.py",
        "retrieval.py",
        "table_chunks.py",
        "retrieval_check.py",
        "corpus.py",
        "portfolio_eval.py",
        "local_smoke.py",
    )
    return {
        "manifest_sha256": sha256(MANIFEST),
        "corpus_sha256": sha256(CATALOG),
        "lockfile_sha256": sha256(ROOT / "uv.lock"),
        "model": MODEL,
        "options": OPTIONS,
        "system": SYSTEM,
        "schema": ANSWER_SCHEMA,
        "chunk_mode": "table-v1",
        "query_mode": "financial-v1",
        "context_mode": "statement-filtered",
        "methods": ["dense", "hybrid"],
        "implementation_sha256": {n: sha256(ROOT / "scripts" / n) for n in names},
    }


def summarize(records):
    result = {}
    for method in ("dense", "hybrid"):
        rows = [r for r in records if r["method"] == method]
        positive = [r for r in rows if r["answerable"]]
        negative = [r for r in rows if not r["answerable"]]
        metrics = (
            "recall_at_5",
            "recall_at_10",
            "mrr_at_10",
            "marker_hit_at_10",
            "selected_marker_hit",
        )
        item = {
            "questions": len(rows),
            "answerable": len(positive),
            "unanswerable": len(negative),
            "service_or_run_errors": sum("error" in r for r in rows),
        }
        for name in metrics:
            item[name] = sum(r.get("retrieval_metrics", {}).get(name, 0) for r in positive) / max(
                1, len(positive)
            )
        if any("passed" in r for r in rows):
            item["numeric_check_passes"] = sum(r.get("passed", False) for r in positive)
            item["refusal_check_passes"] = sum(r.get("passed", False) for r in negative)
            item["false_refusals"] = sum(
                r.get("answer", {}).get("status") == "insufficient_evidence" for r in positive
            )
            item["scope_refusals"] = sum(r.get("generation_skipped", False) for r in rows)
        for key in ("retrieval_seconds", "wall_seconds"):
            times = [r[key] for r in rows if key in r]
            if times:
                item[key] = {
                    "n": len(times),
                    "p50": float(np.percentile(times, 50)),
                    "p95": float(np.percentile(times, 95)),
                }
        result[method] = item
    return result


def evaluate(split, stage, allow_gpu=False):
    if stage == "rag" and not allow_gpu:
        raise ValueError(
            "Model evaluation requires --allow-gpu after coordinating GPU availability"
        )
    config = configuration()
    if split == "final":
        if not FREEZE.exists() or json.loads(FREEZE.read_text()) != config:
            raise ValueError("Final evaluation requires an unchanged frozen configuration")
    cases = [c for c in json.loads(MANIFEST.read_text())["cases"] if c["split"] == split]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = ROOT / "artifacts/portfolio" / f"{stamp}-{split}-{stage}.json"
    trace = ROOT / ".cache/portfolio" / output.name
    for path in (output, trace):
        path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "at_utc": stamp,
        "split": split,
        "stage": stage,
        "config": config,
        "scope": "small authored numeric-QA evaluation; not a FinanceBench benchmark",
        "api_cost_usd": 0,
        "cost_note": "Local inference only; electricity not measured",
        "indexes": {},
        "results": [],
        "expected_records": len(cases) * 2,
        "completed": False,
    }

    def save():
        report["summary"] = summarize(report["results"])
        trace.write_text(json.dumps(report, indent=2), encoding="utf-8")
        public = {**report, "private_trace_sha256": sha256(trace)}
        public["results"] = [
            {k: v for k, v in r.items() if k not in ("messages", "raw_response")}
            for r in report["results"]
        ]
        output.write_text(json.dumps(public, indent=2), encoding="utf-8")

    try:
        if stage == "rag":
            report["ollama_version"] = api("/api/version")
            report["installed_models"] = api("/api/tags")
        for doc_id in dict.fromkeys(c["document_id"] for c in cases):
            print(f"Preparing {doc_id} (CPU)", flush=True)
            retriever, tokenizer, setup = build_index("table-v1", doc_id)
            report["indexes"][doc_id] = setup
            chunks = {c.id: asdict(c) for c in retriever.chunks}
            reader = PdfReader(pdf_path(doc_id))
            for case in (c for c in cases if c["document_id"] == doc_id):
                for method in ("dense", "hybrid"):
                    row = {
                        "case_id": case["id"],
                        "document_id": doc_id,
                        "method": method,
                        "question": case["question"],
                        "answerable": case["value"] is not None,
                    }
                    begin = time.perf_counter()
                    try:
                        if stage == "rag":
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
                                            method=method,
                                        )
                                    )
                            finally:
                                row["gpu_samples"] = monitor.samples
                                row["gpu_sampling_errors"] = monitor.errors
                                row["device_peak_used_mib"] = max(
                                    (
                                        gpu["used_mib"]
                                        for sample in monitor.samples
                                        for gpu in sample["gpus"]
                                    ),
                                    default=None,
                                )
                            row["passed"] = row["structurally_valid"] and score(row["answer"], case)
                            hits = [chunks[h["id"]] for h in row["retrieved"]]
                            selected = [chunks[i] for i in row["supplied_ids"]]
                        else:
                            query = prepare_query(case["question"], "financial-v1")
                            hits = retriever.search(query, method, limit=10)
                            row["retrieval_seconds"] = time.perf_counter() - begin
                            selected = select_context(case["question"], hits)
                            row["retrieved"] = [
                                {k: v for k, v in h.items() if k != "text"} for h in hits
                            ]
                            row["supplied_ids"] = [h["id"] for h in selected]
                        if case["value"] is not None:

                            def marker_hit(items, case=case):
                                return any(
                                    h["pdf_page"] in case["evidence_pages"]
                                    and all(
                                        normalize(m).lower() in normalize(h["text"]).lower()
                                        for m in case["markers"]
                                    )
                                    for h in items
                                )

                            row["retrieval_metrics"] = {
                                **page_metrics(hits, doc_id, case["evidence_pages"]),
                                "marker_hit_at_10": marker_hit(hits[:10]),
                                "selected_marker_hit": marker_hit(selected),
                            }
                    except Exception as error:
                        row.update(error=str(error), passed=False)
                    row["wall_seconds"] = time.perf_counter() - begin
                    report["results"].append(row)
                    save()
                    print(
                        case["id"],
                        method,
                        row.get("passed", row.get("retrieval_metrics")),
                        flush=True,
                    )
    except KeyboardInterrupt:
        report["run_error"] = "Interrupted before completion"
    except Exception as error:
        report["run_error"] = str(error)
    finally:
        if stage == "rag":
            try:
                api("/api/generate", {"model": MODEL, "keep_alive": 0})
                report["after_unload"] = api("/api/ps")
                if any(
                    m.get("name") == MODEL or m.get("model") == MODEL
                    for m in report["after_unload"].get("models", [])
                ):
                    raise RuntimeError("Model remains loaded after cleanup")
            except Exception as error:
                report["unload_error"] = str(error)
        report["completed"] = (
            len(report["results"]) == report["expected_records"] and "run_error" not in report
        )
        save()
    print(f"Report: {output}", flush=True)
    return int(
        "run_error" in report
        or "unload_error" in report
        or len(report["results"]) != len(cases) * 2
        or any("error" in r for r in report["results"])
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("development", "final"), default="development")
    parser.add_argument("--stage", choices=("retrieval", "rag"), default="retrieval")
    parser.add_argument("--allow-gpu", action="store_true")
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        with FREEZE.open("x", encoding="utf-8") as stream:
            json.dump(configuration(), stream, indent=2)
        print(f"Frozen: {FREEZE}")
    else:
        raise SystemExit(evaluate(args.split, args.stage, args.allow_gpu))
