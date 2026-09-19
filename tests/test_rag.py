from types import SimpleNamespace

import pytest

from scripts.rag import select_context, validate_answer, verify_source
from scripts.rag_check import score


def hit():
    return {
        "id": "doc:p1:row1",
        "document_id": "doc",
        "pdf_page": 1,
        "start_char": 21,
        "end_char": 32,
        "header_start_char": 0,
        "header_end_char": 20,
        "extraction_mode": "layout",
        "text": "(Millions) 2018 2017\nCapex 10 20",
    }


def answer():
    return {
        "status": "answered",
        "answer": "2018 capex was USD 10 million.",
        "value": 10,
        "unit": "USD millions",
        "chunk_id": "doc:p1:row1",
        "document_id": "doc",
        "pdf_page": 1,
        "quote": "Capex 10 20",
    }


def test_source_spans_reconstructed_separately():
    reader = SimpleNamespace(pages=[SimpleNamespace(extract_text=lambda **_: hit()["text"])])
    assert verify_source(hit(), reader) == ["(Millions) 2018 2017", "Capex 10 20"]
    changed = {**hit(), "text": "2018 2017 Capex 99 20"}
    with pytest.raises(ValueError, match="source spans"):
        verify_source(changed, reader)


def test_valid_citation():
    assert all(
        validate_answer(answer(), [hit()], {hit()["id"]: ["2018 2017", "Capex 10 20"]}).values()
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("pdf_page", 2),
        ("pdf_page", True),
        ("document_id", "other"),
        ("chunk_id", "not-retrieved"),
        ("quote", "2017 Capex 10"),
        ("quote", "2018 2017"),
        ("value", True),
        ("value", float("nan")),
        ("status", "unknown"),
        ("unit", "USD"),
    ],
)
def test_invalid_payload_or_citation_rejected(field, value):
    changed = {**answer(), field: value}
    assert not all(
        validate_answer(changed, [hit()], {hit()["id"]: ["2018 2017", "Capex 10 20"]}).values()
    )


def test_refusal_requires_no_value_or_citation():
    refusal = {
        **answer(),
        "status": "insufficient_evidence",
        "value": None,
        "document_id": None,
        "pdf_page": None,
        "chunk_id": None,
        "unit": "",
        "quote": "",
    }
    assert all(validate_answer(refusal, [], {}).values())
    refusal["chunk_id"] = "made-up"
    assert not all(validate_answer(refusal, [], {}).values())


def test_context_is_ranked_prefix_and_never_part_of_a_chunk():
    hits = [{**hit(), "id": str(i), "text": "x" * 4000} for i in range(10)]
    selected = select_context("capex?", hits)
    assert 0 < len(selected) < 10
    assert selected == hits[: len(selected)]
    with pytest.raises(ValueError, match="budget"):
        select_context("x" * 20000, hits)


def test_evaluation_checks_units_and_does_not_accept_refusal_for_answerable_case():
    case = {"value": 10, "unit": "USD millions"}
    assert score(answer(), case)
    assert not score({**answer(), "unit": "USD billions"}, case)
    assert not score({**answer(), "status": "insufficient_evidence"}, case)


def test_schema_failure_is_reported():
    assert validate_answer([], [], {}) == {"schema": False}


def test_pipeline_uses_retrieved_text_and_rejects_truncated_response(monkeypatch):
    import json

    from scripts import rag

    captured = {}

    def fake_api(path, payload, timeout):
        captured.update(payload)
        return {
            "message": {"content": json.dumps(answer())},
            "done": True,
            "done_reason": "length",
            "prompt_eval_count": 100,
        }

    monkeypatch.setattr(rag, "api", fake_api)
    retriever = SimpleNamespace(search=lambda *a, **k: [hit()])
    tokenizer = SimpleNamespace(encode=lambda text: SimpleNamespace(ids=[1]))
    reader = SimpleNamespace(pages=[SimpleNamespace(extract_text=lambda **_: hit()["text"])])
    result = rag.answer_question("What was 3M's 2018 capex?", retriever, tokenizer, reader)
    user = json.loads(captured["messages"][1]["content"])
    assert set(user) == {"question", "evidence"}
    assert user["evidence"][0]["text"] == hit()["text"]
    assert result["checks"]["source_quote"]
    assert not result["structurally_valid"]


def test_failure_still_unloads_and_persists_report(monkeypatch, tmp_path):
    from scripts import rag_check

    monkeypatch.setattr(rag_check, "ROOT", tmp_path)
    monkeypatch.setattr(rag_check, "sha256", lambda path: "test-hash")
    calls = []

    def fake_api(path, payload=None):
        calls.append((path, payload))
        return {"models": []}

    def fail_setup(mode):
        raise RuntimeError("setup failed")

    monkeypatch.setattr(rag_check, "api", fake_api)
    monkeypatch.setattr(rag_check, "build_index", fail_setup)
    assert rag_check.main() == 1
    assert ("/api/generate", {"model": rag_check.MODEL, "keep_alive": 0}) in calls
    assert list((tmp_path / "artifacts/rag").glob("*.json"))
def test_answer_schema_has_unique_required_fields_without_mutating_smoke_schema():
    from scripts.local_smoke import SCHEMA
    from scripts.rag import ANSWER_SCHEMA

    for branch in ANSWER_SCHEMA["oneOf"]:
        assert len(branch["required"]) == len(set(branch["required"]))
        assert branch["required"].count("chunk_id") == 1
    assert all("chunk_id" not in branch["required"] for branch in SCHEMA["oneOf"])
