from __future__ import annotations

import re

from models import Entity, Relation


ALLOWED_ENTITY_TYPES = {
    "person",
    "organization",
    "product",
    "concept",
    "location",
    "event",
    "document",
    "technology",
    "other",
}


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split()).strip()


def slugify(value: str) -> str:
    value = normalize_whitespace(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def to_entity_type(value: str) -> str:
    entity_type = slugify(value).replace("-", "_")
    return entity_type if entity_type in ALLOWED_ENTITY_TYPES else "other"


def to_relation_type(value: str) -> str:
    relation_type = normalize_whitespace(value).lower()
    relation_type = re.sub(r"[^a-z0-9]+", "_", relation_type)
    relation_type = re.sub(r"_+", "_", relation_type).strip("_")
    return relation_type


def normalize_extractions(raw_extractions: list[dict]) -> tuple[list[Entity], list[Relation]]:
    entities_by_id: dict[str, Entity] = {}
    relation_keys: set[tuple[str, str, str, str]] = set()
    relations: list[Relation] = []

    for record in raw_extractions:
        chunk_id = record["chunk_id"]
        parsed = record.get("parsed", {})

        for item in parsed.get("entities", []):
            name = normalize_whitespace(str(item.get("name", "")))
            if not name:
                continue

            entity_id = slugify(name)
            if not entity_id:
                continue

            candidate = Entity(
                id=entity_id,
                name=name,
                type=to_entity_type(str(item.get("type", "other"))),
            )
            existing = entities_by_id.get(entity_id)
            if existing is None:
                entities_by_id[entity_id] = candidate
            elif existing.type == "other" and candidate.type != "other":
                entities_by_id[entity_id] = candidate

        for item in parsed.get("relations", []):
            source_name = normalize_whitespace(str(item.get("source", "")))
            target_name = normalize_whitespace(str(item.get("target", "")))
            relation_name = to_relation_type(str(item.get("relation", "")))

            source_id = slugify(source_name)
            target_id = slugify(target_name)

            if not source_id or not target_id or not relation_name:
                continue
            if source_id not in entities_by_id or target_id not in entities_by_id:
                continue

            key = (source_id, target_id, relation_name, chunk_id)
            if key in relation_keys:
                continue

            relation_keys.add(key)
            relations.append(
                Relation(
                    source=source_id,
                    target=target_id,
                    relation=relation_name,
                    chunk_id=chunk_id,
                )
            )

    entities = sorted(entities_by_id.values(), key=lambda entity: entity.id)
    relations = sorted(relations, key=lambda relation: (relation.source, relation.target, relation.relation, relation.chunk_id))
    return entities, relations
