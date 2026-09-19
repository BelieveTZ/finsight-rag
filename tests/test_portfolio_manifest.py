import json

from scripts.corpus import ROOT, document


def test_frozen_portfolio_split_and_annotation_contract():
    cases = json.loads((ROOT / "evaluation/portfolio_v1.json").read_text())["cases"]
    assert len(cases) == len({c["id"] for c in cases}) == 30
    assert sum(c["value"] is not None for c in cases) == 24
    for split in ("development", "final"):
        group = [c for c in cases if c["split"] == split]
        assert len(group) == 15
        assert sum(c["value"] is None for c in group) == 3
        for case in group:
            doc = document(case["document_id"])
            assert doc["split"] == split
            if case["value"] is None:
                assert case["reason"] and not case["evidence_pages"]
            else:
                assert case["markers"] and case["source"]
                assert all(1 <= p <= doc["pdf_pages"] for p in case["evidence_pages"])
