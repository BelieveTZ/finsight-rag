"""Conservative statement-page chunks with repeated source headers, not inferred cells."""

import re
from dataclasses import dataclass

from scripts.retrieval import CHUNK_TOKENS, Chunk, normalize


@dataclass(frozen=True)
class TableChunk(Chunk):
    header_start_char: int
    header_end_char: int
    extraction_mode: str = "layout"


def year_header(line):
    return len(set(re.findall(r"\b(?:19|20)\d{2}\b", line))) >= 2 and bool(
        re.search(r"\b(?:19|20)\d{2}\s{2,}(?:19|20)\d{2}\b", line)
    )


def split_statement(layout, document_id, pdf_page, tokenizer, budget=CHUNK_TOKENS):
    """Return None to keep the original page when detection or row packing is ambiguous.

    Offsets reference normalize(layout). start/end are the body span; the separate
    header span precedes it. Text retains row breaks, so compare normalized spans.
    """
    lines = [line.strip() for line in layout.splitlines() if line.strip()]
    if not any(re.match(r"^Consolidated (?:Statements? of|Balance)", s) for s in lines[:10]):
        return None
    headers = [i for i, s in enumerate(lines) if year_header(s)]
    if len(headers) != 1 or headers[0] >= 20:
        return None
    boundary = headers[0] + 1
    lines = [normalize(s) for s in lines]
    header = "\n".join(lines[:boundary])
    header_end = len(" ".join(lines[:boundary]))
    if len(tokenizer.encode(header).ids) > budget // 2 or boundary == len(lines):
        return None
    offsets, cursor = [], 0
    for line in lines:
        offsets.append(cursor)
        cursor += len(line) + 1
    chunks = []
    start = boundary
    for end in range(boundary, len(lines)):
        candidate = header + "\n" + "\n".join(lines[start : end + 1])
        if len(tokenizer.encode(candidate).ids) <= budget:
            continue
        if start == end:
            return None
        chunks.append(
            TableChunk(
                f"{document_id}:p{pdf_page}:row{start}",
                document_id,
                pdf_page,
                offsets[start],
                offsets[end] - 1,
                header + "\n" + "\n".join(lines[start:end]),
                0,
                header_end,
            )
        )
        start = end
        if len(tokenizer.encode(header + "\n" + lines[start]).ids) > budget:
            return None
    chunks.append(
        TableChunk(
            f"{document_id}:p{pdf_page}:row{start}",
            document_id,
            pdf_page,
            offsets[start],
            cursor - 1,
            header + "\n" + "\n".join(lines[start:]),
            0,
            header_end,
        )
    )
    return chunks
