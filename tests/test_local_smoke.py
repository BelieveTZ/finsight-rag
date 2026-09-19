from scripts.local_smoke import DOC, PDF_PAGE, check_answer, load_evidence


def valid_answer():
    return {
        "status": "answered",
        "answer": "FY2018: USD 1577 million.",
        "value": 1577,
        "unit": "USD millions",
        "document_id": DOC,
        "pdf_page": PDF_PAGE,
        "quote": "PP&E (1,577)",
    }


def test_correct_number_does_not_hide_invalid_citation():
    answer = valid_answer()
    answer["pdf_page"] = 59
    checks = check_answer(answer, 1577, "PP&E (1,577)")
    assert checks["correct_value"]
    assert not checks["correct_page"]


def test_quote_must_be_present_in_evidence():
    checks = check_answer(valid_answer(), 1577, "A different statement.")
    assert not checks["verbatim_quote"]


def test_whitespace_normalized_quote_is_allowed():
    assert all(check_answer(valid_answer(), 1577, "PP&E\n (1,577)").values())


def test_refusal_with_invented_number_fails():
    answer = {
        "status": "insufficient_evidence",
        "answer": "Not disclosed here.",
        "value": 100,
        "unit": "",
        "document_id": None,
        "pdf_page": None,
        "quote": "",
    }
    checks = check_answer(answer, None, "")
    assert checks["refused"]
    assert not checks["no_value"]


def test_correct_refusal():
    answer = {
        "status": "insufficient_evidence",
        "answer": "The excerpt lacks FY2024 data.",
        "value": None,
        "unit": "",
        "document_id": None,
        "pdf_page": None,
        "quote": "",
    }
    assert all(check_answer(answer, None, "").values())


def test_invalid_schema_fails():
    assert not all(check_answer([], 1577, "").values())


def test_refusal_page_zero_is_not_treated_as_missing():
    answer = {
        "status": "insufficient_evidence",
        "answer": "The excerpt lacks FY2024 data.",
        "value": None,
        "unit": "",
        "document_id": None,
        "pdf_page": 0,
        "quote": "",
    }
    assert not check_answer(answer, None, "")["no_fabricated_citation"]


def test_refusal_generation_schema_requires_null_page():
    from scripts.local_smoke import SCHEMA

    refusal = SCHEMA["oneOf"][1]["properties"]
    assert refusal["status"]["enum"] == ["insufficient_evidence"]
    for field in ("value", "document_id", "pdf_page"):
        assert refusal[field] == {"type": "null"}


def test_changed_dataset_rejected(tmp_path):
    import pytest

    path = tmp_path / "data.jsonl"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="hash differs"):
        load_evidence(path)
