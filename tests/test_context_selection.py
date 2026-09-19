import pytest

from scripts.rag import OPTIONS, messages_for, select_context


def candidates(title):
    hits = [
        {
            "id": str(i),
            "document_id": "different_report",
            "pdf_page": i + 1,
            "text": "Segment discussion " + "x" * 1900,
        }
        for i in range(9)
    ]
    hits.append(
        {
            "id": "last",
            "document_id": "different_report",
            "pdf_page": 88,
            "text": title + "\n(Millions) 2022 2021\nAssets 123 120",
        }
    )
    return hits


@pytest.mark.parametrize(
    "question,title",
    [
        ("Use the balance sheet for 2022 assets.", "Consolidated Balance Sheets"),
        (
            "Use the cash flow statement for 2022 purchases.",
            "Consolidated Statement of Cash Flow s",
        ),
    ],
)
def test_requested_statement_at_rank_ten_enters_context(question, title):
    hits = candidates(title)
    selected = select_context(question, hits, "statement-first")
    assert selected[0]["id"] == "last"
    assert selected[1:] == hits[: len(selected) - 1]
    assert sum(len(m["content"].encode("utf-8")) for m in messages_for(question, selected)) <= (
        OPTIONS["num_ctx"] - 2048
    )


def test_unconstrained_question_preserves_ranking():
    hits = candidates("Consolidated Balance Sheets")
    selected = select_context("What were assets in 2022?", hits)
    assert selected == hits[: len(selected)]


def test_statement_mention_in_narrative_does_not_become_a_heading():
    hits = candidates("See the Consolidated Balance Sheets for details.")
    selected = select_context("Use the balance sheet.", hits)
    assert selected == []


def test_legacy_mode_reproduces_missing_low_ranked_statement():
    hits = candidates("Consolidated Balance Sheets")
    selected = select_context("Use the balance sheet.", hits, "ranked-prefix")
    assert "last" not in [h["id"] for h in selected]
    assert selected == hits[: len(selected)]


def test_context_selection_does_not_edit_hits_or_use_page_identity():
    import copy

    hits = candidates("Consolidated Balance Sheets")
    original = copy.deepcopy(hits)
    assert select_context("Use the balance sheet.", hits)[0] == original[-1]
    assert hits == original


def test_unknown_context_mode_rejected():
    with pytest.raises(ValueError, match="mode"):
        select_context("assets?", [], "unknown")


def test_multiple_statement_constraints_keep_baseline_order():
    hits = candidates("Consolidated Balance Sheets")
    selected = select_context("Use the balance sheet and cash flow statement.", hits)
    assert selected == hits[: len(selected)]


def test_explicit_constraint_excludes_other_statement_types():
    hits = candidates("Consolidated Balance Sheets")
    assert select_context("Use the balance sheet.", hits) == hits[-1:]


def test_missing_required_statement_supplies_no_evidence():
    hits = candidates("Consolidated Balance Sheets")
    assert select_context("Use the cash flow statement.", hits) == []
