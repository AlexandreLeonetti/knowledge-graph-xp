from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import BASE_DIR, DATA_DIR, EXTRACTED_DIR, OUTPUT_DIR, settings
from neo4j import GraphDatabase
from normalize import normalize_whitespace, slugify
from pipeline_stage_info import STAGE_INFO, StageInfo
from pdf_loader import load_pdf_pages


@dataclass
class ArtifactStatus:
    name: str
    slug: str
    description: str
    available: bool
    detail: str
    href: str


class ArtifactLoader:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or BASE_DIR
        self.data_dir = DATA_DIR
        self.extracted_dir = EXTRACTED_DIR
        self.output_dir = OUTPUT_DIR

    def load_json_artifact(self, file_name: str, expected_type: type = list) -> dict[str, Any]:
        path = self.extracted_dir / file_name
        if not path.exists():
            return {
                "path": path,
                "exists": False,
                "data": expected_type(),
                "error": None,
            }

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {
                "path": path,
                "exists": True,
                "data": expected_type(),
                "error": f"Could not parse JSON: {exc}",
            }

        if not isinstance(payload, expected_type):
            return {
                "path": path,
                "exists": True,
                "data": expected_type(),
                "error": f"Expected {expected_type.__name__} data in {file_name}.",
            }

        return {"path": path, "exists": True, "data": payload, "error": None}

    def load_chunks(self) -> dict[str, Any]:
        artifact = self.load_json_artifact("chunks.json", list)
        chunks: list[dict[str, Any]] = []

        for index, chunk in enumerate(artifact["data"], start=1):
            if not isinstance(chunk, dict):
                continue
            text = str(chunk.get("text", ""))
            chunks.append(
                {
                    "position": index,
                    "id": str(chunk.get("id", f"chunk-{index:04d}")),
                    "source": str(chunk.get("source", "")),
                    "page_start": chunk.get("page_start"),
                    "page_end": chunk.get("page_end"),
                    "text": text,
                    "char_count": len(text),
                    "word_count": len(text.split()),
                    "line_count": len(text.splitlines()),
                }
            )

        artifact["data"] = chunks
        return artifact

    def load_raw_extractions(self) -> dict[str, Any]:
        artifact = self.load_json_artifact("raw_extractions.json", list)
        rows: list[dict[str, Any]] = []

        for index, record in enumerate(artifact["data"], start=1):
            if not isinstance(record, dict):
                continue

            parsed = record.get("parsed")
            parsed_entities: list[Any] = []
            parsed_relations: list[Any] = []
            warnings: list[str] = []

            if isinstance(parsed, dict):
                raw_entities = parsed.get("entities", [])
                raw_relations = parsed.get("relations", [])
                if isinstance(raw_entities, list):
                    parsed_entities = raw_entities
                else:
                    warnings.append("`parsed.entities` is present but is not a list.")
                if isinstance(raw_relations, list):
                    parsed_relations = raw_relations
                else:
                    warnings.append("`parsed.relations` is present but is not a list.")
            elif parsed is None:
                warnings.append("No parsed payload was stored for this chunk.")
            else:
                warnings.append("The parsed payload exists but is not a JSON object.")

            response_text = record.get("response_text", "")
            if not response_text:
                warnings.append("The raw model response is missing.")

            rows.append(
                {
                    "position": index,
                    "chunk_id": str(record.get("chunk_id", f"chunk-{index:04d}")),
                    "page_start": record.get("page_start"),
                    "page_end": record.get("page_end"),
                    "response_text": response_text if isinstance(response_text, str) else json.dumps(response_text, indent=2, ensure_ascii=False),
                    "parsed": parsed if isinstance(parsed, dict) else {},
                    "parsed_entities": parsed_entities,
                    "parsed_relations": parsed_relations,
                    "warnings": warnings,
                }
            )

        artifact["data"] = rows
        return artifact

    def load_entities(self) -> dict[str, Any]:
        artifact = self.load_json_artifact("entities.json", list)
        entities: list[dict[str, Any]] = []
        for entity in artifact["data"]:
            if not isinstance(entity, dict):
                continue
            entities.append(
                {
                    "id": str(entity.get("id", "")),
                    "name": str(entity.get("name", "")),
                    "type": str(entity.get("type", "other")),
                }
            )
        artifact["data"] = entities
        return artifact

    def load_relations(self) -> dict[str, Any]:
        artifact = self.load_json_artifact("relations.json", list)
        relations: list[dict[str, Any]] = []
        for relation in artifact["data"]:
            if not isinstance(relation, dict):
                continue
            relations.append(
                {
                    "source": str(relation.get("source", "")),
                    "target": str(relation.get("target", "")),
                    "relation": str(relation.get("relation", "")),
                    "chunk_id": str(relation.get("chunk_id", "")),
                }
            )
        artifact["data"] = relations
        return artifact

    def find_source_pdf(self, chunks: list[dict[str, Any]]) -> Path | None:
        source_name = ""
        if chunks:
            source_name = str(chunks[0].get("source", "")).strip()

        candidates: list[Path] = []
        if source_name:
            candidates.append(self.data_dir / "input" / source_name)
            candidates.append(self.base_dir / source_name)

        pdfs = sorted((self.data_dir / "input").glob("*.pdf"))
        if len(pdfs) == 1:
            candidates.append(pdfs[0])

        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def load_pdf_extraction(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        pdf_path = self.find_source_pdf(chunks)
        if pdf_path is None:
            return {
                "available": False,
                "pdf_path": None,
                "pages": [],
                "error": "The source PDF could not be located from the saved artifacts.",
            }

        try:
            pages = load_pdf_pages(pdf_path)
        except Exception as exc:
            return {
                "available": False,
                "pdf_path": pdf_path,
                "pages": [],
                "error": f"Could not read the source PDF: {exc}",
            }

        records = [
            {
                "page_number": page.get("page_number"),
                "text": page.get("text", ""),
                "char_count": len(str(page.get("text", ""))),
                "word_count": len(str(page.get("text", "")).split()),
            }
            for page in pages
            if isinstance(page, dict)
        ]
        return {"available": True, "pdf_path": pdf_path, "pages": records, "error": None}

    def load_graph_artifact(self) -> dict[str, Any]:
        path = self.output_dir / "graph.html"
        return {"path": path, "exists": path.exists()}

    def load_graph_html(self) -> str | None:
        artifact = self.load_graph_artifact()
        path: Path = artifact["path"]
        if not artifact["exists"]:
            return None

        html = path.read_text(encoding="utf-8")
        return html.replace('src="lib/', 'src="/lib/').replace('href="lib/', 'href="/lib/')

    def get_stage_info(self, key: str) -> StageInfo:
        return STAGE_INFO[key]

    def build_entity_mentions(self, raw_rows: list[dict[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in raw_rows:
            for item in row.get("parsed_entities", []):
                if not isinstance(item, dict):
                    continue
                name = normalize_whitespace(str(item.get("name", "")))
                entity_id = slugify(name)
                if entity_id:
                    counts[entity_id] = counts.get(entity_id, 0) + 1
        return counts

    def build_normalization_view(self) -> dict[str, Any]:
        entities_artifact = self.load_entities()
        relations_artifact = self.load_relations()
        raw_artifact = self.load_raw_extractions()

        mentions_by_entity = self.build_entity_mentions(raw_artifact["data"])
        entities = [
            {
                **entity,
                "mentions_count": mentions_by_entity.get(entity["id"], 0),
            }
            for entity in entities_artifact["data"]
        ]

        entity_names = {entity["id"]: entity["name"] for entity in entities}
        relations = [
            {
                **relation,
                "source_name": entity_names.get(relation["source"], relation["source"]),
                "target_name": entity_names.get(relation["target"], relation["target"]),
            }
            for relation in relations_artifact["data"]
        ]

        return {
            "entities_artifact": entities_artifact,
            "relations_artifact": relations_artifact,
            "entities": entities,
            "relations": relations,
            "entity_count": len(entities),
            "relation_count": len(relations),
        }

    def probe_neo4j(self, expected_entity_count: int, expected_relation_count: int) -> dict[str, str]:
        configured = all(
            [
                settings.neo4j_uri,
                settings.neo4j_username,
                settings.neo4j_password,
            ]
        )
        if not configured:
            return {
                "label": "Not configured",
                "detail": "Neo4j credentials are not available in `.env`.",
            }

        driver = None
        try:
            driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.neo4j_password),
            )
            with driver.session() as session:
                entity_count = session.run("MATCH (e:Entity) RETURN count(e) AS count").single()["count"]
                relation_count = session.run("MATCH ()-[r:RELATED]->() RETURN count(r) AS count").single()["count"]
        except Exception as exc:
            return {"label": "Unavailable", "detail": f"Could not query Neo4j: {exc}"}
        finally:
            try:
                driver.close()
            except Exception:
                pass

        if entity_count == expected_entity_count and relation_count == expected_relation_count:
            detail = f"Neo4j has {entity_count} entities and {relation_count} relations. Counts match the saved normalized artifacts."
        else:
            detail = (
                f"Neo4j has {entity_count} entities and {relation_count} relations. "
                f"Saved artifacts have {expected_entity_count} entities and {expected_relation_count} relations."
            )

        return {"label": "Reachable", "detail": detail}

    def build_stage_statuses(self, neo4j_status: dict[str, str] | None = None) -> list[ArtifactStatus]:
        chunks_artifact = self.load_chunks()
        raw_artifact = self.load_raw_extractions()
        normalization_view = self.build_normalization_view()
        pdf_view = self.load_pdf_extraction(chunks_artifact["data"])
        graph_artifact = self.load_graph_artifact()
        storage_status = neo4j_status or self.probe_neo4j(
            normalization_view["entity_count"],
            normalization_view["relation_count"],
        )

        return [
            ArtifactStatus(
                name="PDF extraction",
                slug="pdf-extraction",
                description="This is the plain text recovered from each PDF page before chunking.",
                available=pdf_view["available"],
                detail=f"{len(pdf_view['pages'])} extracted pages" if pdf_view["available"] else pdf_view["error"],
                href="/pdf-extraction",
            ),
            ArtifactStatus(
                name="Chunking",
                slug="chunks",
                description="Chunks are the text windows sent to the model.",
                available=chunks_artifact["exists"] and not chunks_artifact["error"] and len(chunks_artifact["data"]) > 0,
                detail=f"{len(chunks_artifact['data'])} chunks" if chunks_artifact["data"] else "Chunk artifact not available yet.",
                href="/chunks",
            ),
            ArtifactStatus(
                name="Raw extraction",
                slug="raw-extractions",
                description="Raw extraction is the model output before cleanup or deduplication.",
                available=raw_artifact["exists"] and not raw_artifact["error"] and len(raw_artifact["data"]) > 0,
                detail=f"{len(raw_artifact['data'])} raw extraction records" if raw_artifact["data"] else "Raw extraction artifact not available yet.",
                href="/raw-extractions",
            ),
            ArtifactStatus(
                name="Normalization",
                slug="normalization",
                description="Normalization merges inconsistent names into cleaner graph objects.",
                available=normalization_view["entity_count"] > 0 or normalization_view["relation_count"] > 0,
                detail=(
                    f"{normalization_view['entity_count']} entities, "
                    f"{normalization_view['relation_count']} relations"
                ),
                href="/normalization",
            ),
            ArtifactStatus(
                name="Graph storage",
                slug="graph-storage",
                description="This writes the normalized entities and relations into Neo4j using Cypher upserts.",
                available=storage_status["label"] == "Reachable",
                detail=f"{storage_status['label']}: {storage_status['detail']}",
                href="/monitor",
            ),
            ArtifactStatus(
                name="Graph visualization",
                slug="graph",
                description="This reuses the generated HTML graph so you can inspect the final network view.",
                available=graph_artifact["exists"],
                detail="Generated HTML graph is available." if graph_artifact["exists"] else "Graph HTML not available yet.",
                href="/graph",
            ),
            ArtifactStatus(
                name="Monitoring UI",
                slug="monitor-ui",
                description="This FastAPI and Jinja2 layer reads saved artifacts and explains the pipeline in a read-only view.",
                available=True,
                detail="The monitoring UI is available when this app is running.",
                href="/monitor",
            ),
        ]

    def build_home_view(self) -> dict[str, Any]:
        chunks_artifact = self.load_chunks()
        raw_artifact = self.load_raw_extractions()
        normalization_view = self.build_normalization_view()
        pdf_view = self.load_pdf_extraction(chunks_artifact["data"])
        graph_artifact = self.load_graph_artifact()
        neo4j_status = self.probe_neo4j(
            expected_entity_count=normalization_view["entity_count"],
            expected_relation_count=normalization_view["relation_count"],
        )

        source_name = chunks_artifact["data"][0]["source"] if chunks_artifact["data"] else None
        total_pages = len(pdf_view["pages"]) if pdf_view["available"] else None
        stages = self.build_stage_statuses(neo4j_status=neo4j_status)

        return {
            "source_name": source_name,
            "total_pages": total_pages,
            "total_chunks": len(chunks_artifact["data"]),
            "total_raw_records": len(raw_artifact["data"]),
            "total_entities": normalization_view["entity_count"],
            "total_relations": normalization_view["relation_count"],
            "neo4j_status": neo4j_status,
            "graph_available": graph_artifact["exists"],
            "stages": stages,
            "stage_info": STAGE_INFO,
            "artifacts": {
                "chunks": chunks_artifact,
                "raw": raw_artifact,
                "entities": normalization_view["entities_artifact"],
                "relations": normalization_view["relations_artifact"],
                "graph": graph_artifact,
            },
        }
