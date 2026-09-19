import pytest

from scripts.answer_guards import question_checks, scope_error
from scripts.corpus import document, documents, pdf_path


def test_registry_has_disjoint_development_and_final_documents():
    items = documents()
    assert len(items) == len({d["document_id"] for d in items}) == 4
    assert {d["split"] for d in items} == {"development", "final"}
    assert all(len(d["pdf_sha256"]) == 64 and d["pdf_pages"] > 0 for d in items)
    assert all("questions" not in d and "answers" not in d for d in items)


def test_unknown_document_and_path_traversal_rejected():
    with pytest.raises(ValueError):
        pdf_path("../../private")


@pytest.mark.parametrize(
    "doc_id,company",
    [
        ("AMD_2022_10K", "AMD"),
        ("CVSHEALTH_2022_10K", "CVS Health"),
        ("PEPSICO_2022_10K", "PepsiCo"),
    ],
)
def test_scope_follows_selected_document(doc_id, company):
    doc = document(doc_id)
    assert scope_error(f"What was {company}'s 2022 revenue?", doc) is None
    assert scope_error("What was 3M's 2018 revenue?", doc)
    assert scope_error(f"What was {company}'s 2025 revenue?", doc)
    assert question_checks(
        f"{company} 2022 assets",
        {"unit": "USD millions"},
        {"text": "2022", "document_id": doc_id},
        doc,
    )["corpus_document"]
