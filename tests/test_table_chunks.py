import pytest
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace

from scripts.retrieval import normalize
from scripts.table_chunks import split_statement


@pytest.fixture
def tokenizer():
    value = Tokenizer(WordLevel({"[UNK]": 0}, unk_token="[UNK]"))
    value.pre_tokenizer = Whitespace()
    return value


HEADER = "Acme\nConsolidated Statement of Income\nMillions    2022    2021\n"


def test_every_row_has_source_header_and_valid_spans(tokenizer):
    rows = [f"Metric{i}     {i + 10}    {i + 20}" for i in range(20)]
    source = HEADER + "\n".join(rows)
    chunks = split_statement(source, "acme", 3, tokenizer, budget=24)
    assert len(chunks) > 1
    assert len({c.id for c in chunks}) == len(chunks)
    for chunk in chunks:
        assert chunk.pdf_page == 3
        assert "Millions 2022 2021" in chunk.text
        assert len(tokenizer.encode(chunk.text).ids) <= 24
        normalized = normalize(source)
        expected = normalized[chunk.header_start_char : chunk.header_end_char] + " "
        expected += normalized[chunk.start_char : chunk.end_char]
        assert normalize(chunk.text) == expected
    bodies = " ".join(normalize(source)[c.start_char : c.end_char] for c in chunks)
    assert bodies == normalize("\n".join(rows))


@pytest.mark.parametrize(
    "source",
    [
        "Narrative about 2022 and 2021 without a table.",
        "Consolidated Statement of Income\n2022 only\nRevenue 100",
        HEADER + "Revenue 100 90\n2020    2019\nAssets 20 10",
    ],
)
def test_uncertain_headers_fall_back(source, tokenizer):
    assert split_statement(source, "acme", 1, tokenizer) is None


def test_overlong_row_falls_back_without_losing_text(tokenizer):
    assert split_statement(HEADER + "word " * 50, "acme", 1, tokenizer, budget=24) is None


def test_numbers_and_negatives_are_not_rewritten(tokenizer):
    source = HEADER + "Cash payments    (1,234)    (567)"
    chunks = split_statement(source, "acme", 1, tokenizer)
    assert "(1,234) (567)" in chunks[0].text
