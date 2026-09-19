import pytest

from scripts.query_processing import prepare_query


def test_baseline_is_byte_for_byte_unchanged():
    question = "  FY2018 PPNE?\n"
    assert prepare_query(question) == question


@pytest.mark.parametrize("term", ["PPNE", "PP&E", "ppne"])
def test_abbreviations_preserve_year_and_net(term):
    query = prepare_query(f"Acme FY2022 net {term} in EUR billions?", "financial-v1")
    assert "Acme 2022 net property, plant and equipment" in query
    assert "EUR billions" in query


def test_statement_constraint_survives_role_cleanup():
    query = prepare_query(
        "Assume that you are a public equities analyst. "
        "Answer the following question by primarily using information that is shown in the "
        "balance sheet: what is FY2020 net PPNE?",
        "financial-v1",
    )
    assert query.startswith("balance sheet:")
    assert "analyst" not in query
    assert "2020 net property, plant and equipment" in query


def test_capex_and_revenue_aliases_have_no_answers_or_pages():
    query = prepare_query("Compare capex and revenue for Acme FY2021 and FY2022", "financial-v1")
    assert "purchases of property, plant and equipment" in query
    assert "revenue net sales" in query
    assert "Acme 2021 and 2022" in query


def test_negation_scope_units_and_names_are_retained():
    original = "Which revenue does NOT include tax for Acme, excluding 2020, in USD millions?"
    query = prepare_query(original, "financial-v1")
    assert "does NOT include tax for Acme, excluding 2020, in USD millions" in query


def test_unrelated_words_are_not_rewritten():
    assert (
        prepare_query("RevenueCorp FYI population?", "financial-v1")
        == "RevenueCorp FYI population?"
    )


def test_invalid_mode_rejected():
    with pytest.raises(ValueError):
        prepare_query("test", "unknown")
