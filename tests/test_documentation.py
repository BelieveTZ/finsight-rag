import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


def test_relative_markdown_links_resolve():
    root = Path(__file__).resolve().parents[1]
    files = [root / "README.md", *sorted((root / "docs").glob("*.md"))]
    missing = []
    for source in files:
        for target in re.findall(r"\]\(([^\s)]+)\)", source.read_text(encoding="utf-8")):
            parsed = urlsplit(target)
            if not parsed.scheme and parsed.path:
                if not (source.parent / unquote(parsed.path)).exists():
                    missing.append(f"{source.name}: {target}")
    assert not missing, "Broken local documentation links: " + ", ".join(missing)
