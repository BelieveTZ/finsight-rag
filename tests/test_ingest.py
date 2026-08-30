from pathlib import Path

from finsight.ingest import load_text


def test_load_text_reads_chinese_report() -> None:
    report_path = Path("tests/fixtures/sample_report.txt")
    content = load_text(report_path)

    assert "研发费用为 10 亿元" in content