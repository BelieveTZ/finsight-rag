import pytest

from scripts import rag


@pytest.mark.parametrize(
    "question",
    [
        "What was Microsoft's FY2018 revenue in USD millions?",
        "What was 3M's FY2024 revenue?",
        "What was its revenue?",
        "Compare 3M and Microsoft in 2018",
        "What was NVIDIA's 2017 revenue?",
        "What were 3M's 2019 capital expenditures?",
        "Compare 3M revenue in 2017 and 2018",
        "Using 3M's report, what was Microsoft's 2018 revenue?",
    ],
)
def test_unsupported_scope_never_reaches_retrieval(question):
    class Unavailable:
        def __getattr__(self, name):
            raise AssertionError("Out-of-scope question reached inference or retrieval")

    result = rag.answer_question(question, Unavailable(), Unavailable(), Unavailable())
    assert result["answer"]["status"] == "insufficient_evidence"
    assert result["answer"]["answer"].strip()
    assert result["generation_skipped"]


def test_refusal_schema_requires_explanation():
    for branch in rag.ANSWER_SCHEMA["oneOf"]:
        assert branch["properties"]["answer"]["minLength"] >= 1


def test_billions_must_match_quoted_millions():
    answer = {
        "status": "answered",
        "answer": "8.738 billion",
        "value": 8738,
        "unit": "USD billions",
        "document_id": "3M_2018_10K",
        "pdf_page": 58,
        "chunk_id": "p58",
        "quote": "Property, plant and equipment 8,738 8,866",
    }
    hit = {
        "id": "p58",
        "document_id": "3M_2018_10K",
        "pdf_page": 58,
        "text": "(Millions) 2018 2017 Property, plant and equipment 8,738 8,866",
    }
    checks = rag.validate_answer(answer, [hit], {"p58": [hit["text"]]})
    assert not checks["numeric_evidence"]
    answer["value"] = 8.738
    assert rag.validate_answer(answer, [hit], {"p58": [hit["text"]]})["numeric_evidence"]


def test_explicit_billions_in_quote_support_millions_output():
    from scripts.answer_guards import numeric_evidence

    answer = {"value": 3193, "unit": "USD millions", "quote": "Dividends were $3.193 billion."}
    assert numeric_evidence(answer, {"text": answer["quote"]})
    assert not numeric_evidence({**answer, "value": 3.193}, {"text": answer["quote"]})


def test_missing_source_units_fail_closed():
    from scripts.answer_guards import numeric_evidence

    assert not numeric_evidence(
        {"value": 10, "unit": "USD millions", "quote": "Capex 10"}, {"text": "Capex 10"}
    )


def test_statement_constraint_is_checked():
    from scripts.answer_guards import question_checks

    checks = question_checks(
        "What was 3M net PPNE in 2018 using the balance sheet?",
        {"unit": "USD millions"},
        {"document_id": "3M_2018_10K", "text": "2018 segment results"},
    )
    assert not checks["statement_type"]


def test_split_pdf_cash_flow_title_is_recognized():
    from scripts.answer_guards import question_checks

    assert question_checks(
        "What were 3M capital expenditures in 2018 using the cash flow statement?",
        {"unit": "USD millions"},
        {
            "document_id": "3M_2018_10K",
            "text": "Consolidated Statement of Cash Flow s\n(Millions) 2018",
        },
    )["statement_type"]


@pytest.mark.parametrize("title", ["Consolidated Balance Shee t", "Consolidated Balance Sheets"])
def test_split_balance_title_matches_selection_and_validation(title):
    from scripts.answer_guards import question_checks

    question = "What was 3M net PPNE in 2018 using the balance sheet?"
    hit = {
        "id": "p58",
        "document_id": "3M_2018_10K",
        "pdf_page": 58,
        "text": title + "\n(Millions) 2018",
    }
    assert rag.select_context(question, [hit]) == [hit]
    assert question_checks(question, {"unit": "USD millions"}, hit)["statement_type"]


def test_narrative_mention_is_not_a_statement_heading():
    from scripts.answer_guards import question_checks

    assert not question_checks(
        "Use the balance sheet for 3M assets in 2018",
        {"unit": "USD millions"},
        {
            "document_id": "3M_2018_10K",
            "text": "See the Consolidated Balance Sheets for 2018 assets.",
        },
    )["statement_type"]
