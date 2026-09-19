import json
from pathlib import Path

import pytest

from scripts.corpus import document
from scripts.rag_check import main


def test_demo_keeps_original_six_case_acceptance_and_uses_only_development():
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / "evaluation/demo_v1.json").read_text())["cases"]
    assert len(cases) == len({c["id"] for c in cases}) == 6
    assert sum(c["answer_kind"] == "fact" for c in cases) == 2
    assert sum(c["expected_status"] == "insufficient_evidence" for c in cases) == 2
    assert (
        sum(c["answer_kind"] == "numeric" and c["expected_status"] == "answered" for c in cases)
        == 2
    )
    assert all(document(c["document_id"])["split"] == "development" for c in cases)
    assert all(c["review"] for c in cases)


@pytest.mark.parametrize("kwargs", [{"answer_kind": "fact"}, {"document_id": "PEPSICO_2022_10K"}])
def test_nondefault_demo_needs_question_before_services_are_contacted(kwargs):
    with pytest.raises(ValueError, match="question"):
        main(**kwargs)
