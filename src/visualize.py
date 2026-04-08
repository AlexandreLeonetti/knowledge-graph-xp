from __future__ import annotations

from pathlib import Path

import networkx as nx
from pyvis.network import Network

from config import OUTPUT_DIR
from models import Entity, Relation


TYPE_COLORS = {
    "person": "#d97706",
    "organization": "#2563eb",
    "product": "#7c3aed",
    "concept": "#0f766e",
    "location": "#059669",
    "event": "#dc2626",
    "document": "#4f46e5",
    "technology": "#0891b2",
    "other": "#6b7280",
}


def build_networkx_graph(entities: list[Entity], relations: list[Relation]) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()

    for entity in entities:
        graph.add_node(
            entity.id,
            label=entity.name,
            title=f"ID: {entity.id}<br>Type: {entity.type}",
            color=TYPE_COLORS.get(entity.type, TYPE_COLORS["other"]),
        )

    for relation in relations:
        graph.add_edge(
            relation.source,
            relation.target,
            title=f"Relation: {relation.relation}<br>Chunk: {relation.chunk_id}",
            label=relation.relation,
        )

    return graph


def write_graph_html(
    entities: list[Entity],
    relations: list[Relation],
    output_path: Path | None = None,
) -> Path:
    output_file = output_path or OUTPUT_DIR / "graph.html"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    graph = build_networkx_graph(entities, relations)
    network = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="#111827", directed=True)
    network.barnes_hut()

    for node_id, attrs in graph.nodes(data=True):
        network.add_node(node_id, **attrs)

    for source, target, attrs in graph.edges(data=True):
        network.add_edge(source, target, **attrs)

    network.write_html(str(output_file), notebook=False)
    return output_file
