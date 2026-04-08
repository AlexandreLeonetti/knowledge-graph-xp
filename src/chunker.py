from __future__ import annotations

from pathlib import Path

from models import Chunk


def build_chunks(
    pages: list[dict],
    source_path: Path,
    chunk_size: int,
    chunk_overlap: int,
    max_chunks: int | None = None,
) -> list[Chunk]:
    if not pages:
        return []

    combined_parts: list[str] = []
    page_offsets: list[dict] = []
    cursor = 0

    for page in pages:
        page_text = page["text"].strip()
        if not page_text:
            continue
        part = f"[Page {page['page_number']}]\n{page_text}\n\n"
        start = cursor
        end = cursor + len(part)
        page_offsets.append(
            {
                "page_number": page["page_number"],
                "start": start,
                "end": end,
            }
        )
        combined_parts.append(part)
        cursor = end

    combined_text = "".join(combined_parts).strip()
    if not combined_text:
        return []

    step = chunk_size - chunk_overlap
    chunks: list[Chunk] = []
    start = 0
    chunk_index = 1

    while start < len(combined_text):
        end = min(len(combined_text), start + chunk_size)
        chunk_text = combined_text[start:end].strip()
        if chunk_text:
            page_numbers = [
                record["page_number"]
                for record in page_offsets
                if record["end"] > start and record["start"] < end
            ]
            if page_numbers:
                chunks.append(
                    Chunk(
                        id=f"chunk-{chunk_index:04d}",
                        source=source_path.name,
                        page_start=min(page_numbers),
                        page_end=max(page_numbers),
                        text=chunk_text,
                    )
                )
                chunk_index += 1

        if end >= len(combined_text):
            break
        start += step

        if max_chunks is not None and len(chunks) >= max_chunks:
            break

    return chunks
