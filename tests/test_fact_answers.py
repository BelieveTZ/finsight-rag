import copy
import json
from types import SimpleNamespace

import pytest

from scripts import rag
from scripts.answer_guards import refusal

DOC = {"document_id": "REPORT", "company": "Example", "aliases": ["Example"], "year": 2022}
TEXT = "The business sells cereals and snacks. Supplier concentration can disrupt production."
HIT = {
    "id": "REPORT:p1:t0",
    "document_id": "REPORT",
    "pdf_page": 1,
    "start_char": 0,
    "end_char": len(TEXT),
    "text": TEXT,
}
ANSWER = {
    "status": "answered",
    "answer": "The business sells cereals and snacks.",
    "value": None,
    "unit": "",
    "document_id": "REPORT",
    "pdf_page": 1,
    "quote": "The business sells cereals and snacks.",
    "chunk_id": HIT["id"],
}


def test_fact_schema_does_not_relax_numeric_schema():
    numeric = copy.deepcopy(rag.ANSWER_SCHEMA)
    assert rag.answer_profile("fact")[1]["oneOf"][0]["properties"]["value"] == {"type": "null"}
    assert rag.ANSWER_SCHEMA == numeric
    assert rag.ANSWER_SCHEMA["oneOf"][0]["properties"]["value"] == {"type": "number"}


def test_fact_checks_provenance_without_requiring_a_number():
    checks = rag.validate_answer(ANSWER, [HIT], {HIT["id"]: [TEXT]}, "fact")
    assert all(checks.values())
    assert "numeric_evidence" not in checks
    assert not all(rag.validate_answer(ANSWER, [HIT], {HIT["id"]: [TEXT]}).values())


@pytest.mark.parametrize(
    "field,value",
    [
        ("quote", "The business sells aircraft."),
        ("document_id", "OTHER"),
        ("pdf_page", True),
        ("chunk_id", "invented"),
        ("value", 42),
        ("unit", "USD millions"),
        ("answer", "x" * 601),
        ("quote", "x" * 601),
    ],
)
def test_invalid_fact_response_rejected(field, value):
    assert not all(
        rag.validate_answer({**ANSWER, field: value}, [HIT], {HIT["id"]: [TEXT]}, "fact").values()
    )


def test_fact_refusal_payload_is_checked():
    assert all(rag.validate_answer(refusal("Not disclosed."), [], {}, "fact").values())
    invalid = {**refusal("Not disclosed."), "quote": "invented"}
    assert not all(rag.validate_answer(invalid, [], {}, "fact").values())


def test_fact_pipeline_delivers_source_quote_not_unverified_paraphrase(monkeypatch):
    requests = []

    def fake_api(path, payload, timeout):
        requests.append(payload)
        return {
            "message": {"content": json.dumps({**ANSWER, "answer": "Invented paraphrase"})},
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 100,
        }

    monkeypatch.setattr(rag, "api", fake_api)
    retriever = SimpleNamespace(search=lambda *a, **k: [HIT])
    tokenizer = SimpleNamespace(encode=lambda text: SimpleNamespace(ids=[1]))
    reader = SimpleNamespace(pages=[SimpleNamespace(extract_text=lambda **_: TEXT)])
    result = rag.answer_question(
        "What does Example sell in its 2022 report?",
        retriever,
        tokenizer,
        reader,
        document=DOC,
        answer_kind="fact",
    )
    assert result["structurally_valid"]
    assert result["answer"]["answer"].startswith(ANSWER["quote"])
    assert "Invented" not in result["answer"]["answer"]
    assert result["model_answer"]["answer"] == "Invented paraphrase"
    assert requests[0]["format"] == rag.FACT_SCHEMA
    assert set(json.loads(requests[0]["messages"][1]["content"])) == {"question", "evidence"}


def test_fact_mode_only_allows_selected_report_year_without_model_call(monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("Out-of-period fact must not call the model")

    monkeypatch.setattr(rag, "api", unexpected)
    result = rag.answer_question(
        "What did Example sell in 2021?", None, None, None, document=DOC, answer_kind="fact"
    )
    assert result["generation_skipped"] and result["decision"] == "scope_refusal"


def test_unknown_answer_mode_rejected_before_any_service_call():
    with pytest.raises(ValueError, match="mode"):
        rag.answer_question("question", None, None, None, answer_kind="unsupported")


def test_fact_context_respects_its_own_prompt_budget():
    hits = [{**HIT, "id": str(i), "text": "x" * 4000} for i in range(10)]
    selected = rag.select_context("Example 2022 products?", hits, answer_kind="fact")
    size = sum(
        len(m["content"].encode())
        for m in rag.messages_for("Example 2022 products?", selected, "fact")
    )
    assert 0 < len(selected) < len(hits)
    assert size <= rag.OPTIONS["num_ctx"] - 2048


def test_fact_context_preserves_branch_champions_without_altering_numeric_prefix():
    hits = [
        {
            **HIT,
            "id": str(i),
            "text": "x" * 2500,
            "dense_rank": i + 1,
            "lexical_rank": 1 if i == 7 else None,
        }
        for i in range(10)
    ]
    original = copy.deepcopy(hits)
    facts = rag.select_context("Example 2022 risk?", hits, answer_kind="fact")
    numeric = rag.select_context("Example 2022 revenue?", hits)
    assert [h["id"] for h in facts[:2]] == ["0", "7"]
    assert all(h["id"] != "7" for h in numeric)
    assert hits == original
    assert facts == [h for h in sorted(hits, key=lambda h: h["id"] not in {"0", "7"})][: len(facts)]
    prefix = rag.select_context(
        "Example 2022 risk?", hits, mode="ranked-prefix", answer_kind="fact"
    )
    assert prefix == hits[: len(prefix)]
