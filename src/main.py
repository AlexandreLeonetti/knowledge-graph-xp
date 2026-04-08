from __future__ import annotations

import json
from pathlib import Path

import typer

from chunker import build_chunks
from config import EXTRACTED_DIR, OUTPUT_DIR, settings
from extractor import extract_all_chunks
from models import Entity, Relation
from neo4j_store import run_query, store_graph
from normalize import normalize_extractions
from pdf_loader import load_pdf_pages
from visualize import write_graph_html


app = typer.Typer(help="Minimal PDF to knowledge-graph MVP.")


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_entities(path: Path) -> list[Entity]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return [Entity.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]


def load_relations(path: Path) -> list[Relation]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return [Relation.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]


@app.command()
def ingest(pdf_path: str) -> None:
    """Run the full PDF ingestion pipeline."""
    try:
        settings.validate_chunking()

        source_path = Path(pdf_path)
        pages = load_pdf_pages(source_path)
        if not pages:
            raise ValueError(f"No extractable text found in {source_path}")

        chunks = build_chunks(
            pages=pages,
            source_path=source_path,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            max_chunks=settings.max_chunks,
        )
        if not chunks:
            raise ValueError("No chunks were generated from the PDF.")

        raw_extractions = extract_all_chunks(chunks)
        entities, relations = normalize_extractions(raw_extractions)

        write_json(EXTRACTED_DIR / "chunks.json", [chunk.model_dump() for chunk in chunks])
        write_json(EXTRACTED_DIR / "raw_extractions.json", raw_extractions)
        write_json(EXTRACTED_DIR / "entities.json", [entity.model_dump() for entity in entities])
        write_json(EXTRACTED_DIR / "relations.json", [relation.model_dump() for relation in relations])

        store_graph(entities, relations)
        output_file = write_graph_html(entities, relations, OUTPUT_DIR / "graph.html")

        typer.echo(f"Processed {len(chunks)} chunks from {source_path.name}")
        typer.echo(f"Saved {len(entities)} entities and {len(relations)} relations")
        typer.echo(f"Graph HTML written to {output_file}")
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def visualize() -> None:
    """Build graph.html from saved JSON artifacts."""
    try:
        entities = load_entities(EXTRACTED_DIR / "entities.json")
        relations = load_relations(EXTRACTED_DIR / "relations.json")
        output_file = write_graph_html(entities, relations, OUTPUT_DIR / "graph.html")
        typer.echo(f"Graph HTML written to {output_file}")
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def query(cypher: str | None = None) -> None:
    """Run a sample or custom Cypher query."""
    try:
        rows = run_query(cypher=cypher)
        typer.echo(f"Returned {len(rows)} rows")
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
