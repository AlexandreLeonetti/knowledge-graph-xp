from __future__ import annotations

import json
from openai import OpenAI

from config import PROMPTS_DIR, settings
from models import Chunk, ExtractionResult


def load_prompt() -> str:
    prompt_path = PROMPTS_DIR / "extract_graph.txt"
    return prompt_path.read_text(encoding="utf-8").strip()


def build_client() -> OpenAI:
    settings.require_deepseek()
    return OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url.rstrip("/"),
    )


def _clean_json_text(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def parse_extraction(content: str) -> ExtractionResult:
    cleaned = _clean_json_text(content)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned invalid JSON: {exc}") from exc

    try:
        return ExtractionResult.model_validate(payload)
    except Exception as exc:
        raise ValueError(f"Model JSON did not match the expected schema: {exc}") from exc


def extract_chunk_graph(client: OpenAI, prompt_text: str, chunk: Chunk) -> tuple[ExtractionResult, str]:
    response = client.chat.completions.create(
        model=settings.deepseek_model,
        response_format={"type": "json_object"},
        temperature=0,
        messages=[
            {"role": "system", "content": prompt_text},
            {
                "role": "user",
                "content": (
                    f"Chunk ID: {chunk.id}\n"
                    f"Source: {chunk.source}\n"
                    f"Pages: {chunk.page_start}-{chunk.page_end}\n\n"
                    f"Text:\n{chunk.text}"
                ),
            },
        ],
    )

    content = response.choices[0].message.content or ""
    parsed = parse_extraction(content)
    return parsed, content


def extract_all_chunks(chunks: list[Chunk]) -> list[dict]:
    if not chunks:
        return []

    client = build_client()
    prompt_text = load_prompt()
    records: list[dict] = []

    for chunk in chunks:
        try:
            parsed, raw_content = extract_chunk_graph(client, prompt_text, chunk)
        except Exception as exc:
            raise RuntimeError(f"Extraction failed for {chunk.id} (pages {chunk.page_start}-{chunk.page_end}): {exc}") from exc
        records.append(
            {
                "chunk_id": chunk.id,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "response_text": raw_content,
                "parsed": parsed.model_dump(),
            }
        )

    return records
