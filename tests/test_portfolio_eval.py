import json

import pytest

from scripts import portfolio_eval


def test_gpu_stage_requires_explicit_permission():
    with pytest.raises(ValueError, match="allow-gpu"):
        portfolio_eval.evaluate("development", "rag")


def test_freeze_covers_the_numeric_scoring_implementation():
    from scripts.retrieval import sha256

    config = portfolio_eval.configuration()
    assert config["implementation_sha256"]["rag_check.py"] == sha256(
        portfolio_eval.ROOT / "scripts/rag_check.py"
    )


def test_final_requires_matching_frozen_config(monkeypatch, tmp_path):
    monkeypatch.setattr(portfolio_eval, "FREEZE", tmp_path / "missing.json")
    with pytest.raises(ValueError, match="frozen"):
        portfolio_eval.evaluate("final", "retrieval")


def test_summary_keeps_errors_and_refusals_in_denominator():
    rows = [
        {
            "method": "hybrid",
            "answerable": True,
            "passed": True,
            "retrieval_metrics": {"recall_at_10": 1},
            "answer": {"status": "answered"},
        },
        {"method": "hybrid", "answerable": True, "passed": False, "error": "timeout"},
        {
            "method": "hybrid",
            "answerable": True,
            "passed": False,
            "answer": {"status": "insufficient_evidence"},
        },
        {
            "method": "hybrid",
            "answerable": False,
            "passed": True,
            "generation_skipped": True,
            "answer": {"status": "insufficient_evidence"},
        },
    ]
    result = portfolio_eval.summarize(rows)["hybrid"]
    assert result["answerable"] == 3
    assert result["recall_at_10"] == 1 / 3
    assert result["numeric_check_passes"] == result["false_refusals"] == 1
    assert result["service_or_run_errors"] == result["refusal_check_passes"] == 1


def test_setup_failure_is_marked_incomplete_without_touching_gpu(monkeypatch, tmp_path):
    manifest = tmp_path / "questions.json"
    manifest.write_text(json.dumps({"cases": [{"split": "development", "document_id": "doc"}]}))
    monkeypatch.setattr(portfolio_eval, "MANIFEST", manifest)
    monkeypatch.setattr(portfolio_eval, "ROOT", tmp_path)
    monkeypatch.setattr(portfolio_eval, "configuration", lambda: {})

    def fail_setup(*args):
        raise RuntimeError("Missing PDF")

    def unexpected_gpu(*args):
        pytest.fail("CPU retrieval must never call the model service")

    monkeypatch.setattr(portfolio_eval, "build_index", fail_setup)
    monkeypatch.setattr(portfolio_eval, "api", unexpected_gpu)
    assert portfolio_eval.evaluate("development", "retrieval") == 1
    report = json.loads(next((tmp_path / "artifacts/portfolio").glob("*.json")).read_text())
    assert not report["completed"]
    assert report["expected_records"] == 2 and report["results"] == []
    assert report["run_error"] == "Missing PDF"
