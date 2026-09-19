"""CPU-only evidence check for the exposed qualitative demonstration questions."""

import json
from datetime import UTC, datetime

from scripts.corpus import ROOT
from scripts.query_processing import prepare_query
from scripts.rag import FACT_CONTEXT_POLICY, select_context
from scripts.retrieval import page_metrics, sha256
from scripts.retrieval_check import build_index


def main():
    manifest = ROOT / "evaluation/demo_v1.json"
    cases = [c for c in json.loads(manifest.read_text())["cases"] if c["answer_kind"] == "fact"]
    report = {
        "scope": "Exposed development fact retrieval, not generated-answer accuracy",
        "manifest_sha256": sha256(manifest),
        "query_mode": "financial-v1",
        "chunk_mode": "table-v1",
        "answer_kind": "fact",
        "context_mode": "statement-filtered",
        "context_selection_policy": FACT_CONTEXT_POLICY,
        "implementation_sha256": {
            name: sha256(ROOT / "scripts" / name)
            for name in ("rag.py", "retrieval.py", "query_processing.py", "fact_retrieval_check.py")
        },
        "indexes": {},
        "results": [],
    }
    for doc_id in dict.fromkeys(c["document_id"] for c in cases):
        retriever, _, report["indexes"][doc_id] = build_index("table-v1", doc_id)
        for case in (c for c in cases if c["document_id"] == doc_id):
            for method in ("dense", "hybrid"):
                hits = retriever.search(prepare_query(case["question"], "financial-v1"), method)
                selected = select_context(case["question"], hits, answer_kind="fact")
                row = {
                    "case_id": case["id"],
                    "question": case["question"],
                    "method": method,
                    "metrics": page_metrics(hits, doc_id, case["evidence_pages"]),
                    "selected_gold_page": any(
                        h["pdf_page"] in case["evidence_pages"] for h in selected
                    ),
                    "supplied_ids": [h["id"] for h in selected],
                    "retrieved": [{k: v for k, v in h.items() if k != "text"} for h in hits],
                }
                report["results"].append(row)
                print(case["id"], method, row["metrics"], row["selected_gold_page"], flush=True)
    output = (
        ROOT
        / "artifacts/demo"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "-fact-retrieval.json")
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(output, flush=True)


if __name__ == "__main__":
    main()
