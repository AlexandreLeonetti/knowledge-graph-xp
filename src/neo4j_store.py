from __future__ import annotations

from neo4j import GraphDatabase

from config import settings
from models import Entity, Relation


DEFAULT_QUERY = (
    "MATCH (a:Entity)-[r:RELATED]->(b:Entity) "
    "RETURN a.name AS source, r.type AS relation, b.name AS target, r.chunk_id AS chunk_id "
    "LIMIT 10"
)


def get_driver():
    settings.require_neo4j()
    return GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )


def ensure_constraint(driver) -> None:
    query = "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE"
    with driver.session() as session:
        session.run(query)


def upsert_entities(driver, entities: list[Entity]) -> None:
    query = """
    UNWIND $rows AS row
    MERGE (e:Entity {id: row.id})
    SET e.name = row.name, e.type = row.type
    """
    rows = [entity.model_dump() for entity in entities]
    with driver.session() as session:
        session.run(query, rows=rows)


def upsert_relations(driver, relations: list[Relation]) -> None:
    query = """
    UNWIND $rows AS row
    MATCH (source:Entity {id: row.source})
    MATCH (target:Entity {id: row.target})
    MERGE (source)-[r:RELATED {type: row.relation, chunk_id: row.chunk_id}]->(target)
    """
    rows = [relation.model_dump() for relation in relations]
    with driver.session() as session:
        session.run(query, rows=rows)


def store_graph(entities: list[Entity], relations: list[Relation]) -> None:
    driver = get_driver()
    try:
        ensure_constraint(driver)
        upsert_entities(driver, entities)
        upsert_relations(driver, relations)
    finally:
        driver.close()


def run_query(cypher: str | None = None, limit: int = 10) -> list[dict]:
    driver = get_driver()
    query = cypher or DEFAULT_QUERY
    if cypher is None and "LIMIT" not in query.upper():
        query = f"{query} LIMIT {limit}"

    try:
        with driver.session() as session:
            result = session.run(query)
            rows = [record.data() for record in result]
    finally:
        driver.close()

    for row in rows:
        print(row)
    return rows
