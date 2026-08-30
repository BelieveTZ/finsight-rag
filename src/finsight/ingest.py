from pathlib import Path


def load_text(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")