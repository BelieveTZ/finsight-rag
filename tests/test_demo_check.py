import pytest

from scripts.demo_check import automatic_check, evaluate


def test_demo_requires_explicit_gpu_opt_in():
    with pytest.raises(ValueError, match="allow-gpu"):
        evaluate()


def test_fact_automatic_check_requires_valid_source_on_annotated_page():
    case = {"expected_status": "answered", "answer_kind": "fact", "evidence_pages": [5]}
    row = {"structurally_valid": True, "answer": {"status": "answered", "pdf_page": 5}}
    assert automatic_check(row, case)
    row["answer"]["pdf_page"] = 6
    assert not automatic_check(row, case)
    row["answer"]["pdf_page"] = 5
    row["structurally_valid"] = False
    assert not automatic_check(row, case)


def test_numeric_demo_checks_value_and_unit_not_just_answer_status():
    case = {
        "expected_status": "answered",
        "answer_kind": "numeric",
        "value": 10,
        "unit": "USD millions",
    }
    row = {
        "structurally_valid": True,
        "answer": {"status": "answered", "value": 10, "unit": "USD billions"},
    }
    assert not automatic_check(row, case)
    row["answer"]["unit"] = "USD millions"
    assert automatic_check(row, case)
