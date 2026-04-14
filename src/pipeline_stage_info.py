from __future__ import annotations

from dataclasses import dataclass

from config import settings


@dataclass(frozen=True)
class StageInfo:
    key: str
    display_name: str
    performed_by: str
    stage_type: str
    library_or_framework: str
    model_name: str | None
    short_description: str
    interview_explanation: str
    why_it_matters: str


STAGE_INFO: dict[str, StageInfo] = {
    "pdf-extraction": StageInfo(
        key="pdf-extraction",
        display_name="PDF extraction",
        performed_by="PyMuPDF (fitz)",
        stage_type="Deterministic extraction",
        library_or_framework="PyMuPDF",
        model_name=None,
        short_description="Reads each PDF page and extracts plain text before later processing.",
        interview_explanation="We extract raw text page by page from the source PDF using PyMuPDF before any LLM step.",
        why_it_matters="This defines the exact source text the rest of the pipeline can see.",
    ),
    "chunks": StageInfo(
        key="chunks",
        display_name="Chunking",
        performed_by="Custom Python chunker",
        stage_type="Deterministic preprocessing",
        library_or_framework="Project chunking logic",
        model_name=None,
        short_description="Builds overlapping fixed-size text windows across the extracted PDF text.",
        interview_explanation="We split the document into overlapping chunks so the extraction model keeps enough local context across chunk boundaries.",
        why_it_matters="Chunking controls context size, recall, and how much cross-page detail the model can keep.",
    ),
    "raw-extractions": StageInfo(
        key="raw-extractions",
        display_name="Raw extraction",
        performed_by="DeepSeek chat model via OpenAI-compatible client",
        stage_type="LLM-based structured extraction",
        library_or_framework="openai Python SDK",
        model_name=settings.deepseek_model,
        short_description="Sends each chunk to the model with a structured prompt and stores the raw JSON response.",
        interview_explanation="Each chunk is sent to the LLM with a structured extraction prompt, and the model returns JSON entities and relations.",
        why_it_matters="This is the stage that converts unstructured text into candidate graph facts.",
    ),
    "normalization": StageInfo(
        key="normalization",
        display_name="Normalization",
        performed_by="Deterministic Python post-processing",
        stage_type="Deterministic cleanup",
        library_or_framework="Project normalization rules",
        model_name=None,
        short_description="Normalizes whitespace, slugifies canonical IDs, maps entity types, normalizes relation labels, and deduplicates entities and relations.",
        interview_explanation="After LLM extraction, we use deterministic Python cleanup to normalize names and labels, assign canonical IDs, and deduplicate repeated entities and relations.",
        why_it_matters="Deterministic cleanup reduces duplication and makes the graph more queryable.",
    ),
    "graph-storage": StageInfo(
        key="graph-storage",
        display_name="Graph storage",
        performed_by="Neo4j Python driver",
        stage_type="Storage",
        library_or_framework="Neo4j driver",
        model_name=None,
        short_description="Upserts normalized entities and relations into Neo4j with Cypher.",
        interview_explanation="We take the normalized graph objects and store them in Neo4j so they can be queried as nodes and relationships.",
        why_it_matters="This turns extracted facts into a persistent graph database rather than a temporary JSON artifact.",
    ),
    "graph": StageInfo(
        key="graph",
        display_name="Graph visualization",
        performed_by="NetworkX + PyVis",
        stage_type="Visualization",
        library_or_framework="NetworkX and PyVis",
        model_name=None,
        short_description="Builds a graph structure in Python and writes an interactive HTML network view.",
        interview_explanation="We convert the normalized entities and relations into a NetworkX graph, then render an interactive HTML view with PyVis.",
        why_it_matters="Visualization makes the extracted graph inspectable and easier to explain.",
    ),
    "monitor-ui": StageInfo(
        key="monitor-ui",
        display_name="Monitoring UI",
        performed_by="FastAPI + Jinja2 templates",
        stage_type="Web UI",
        library_or_framework="FastAPI and Jinja2",
        model_name=None,
        short_description="Serves read-only pages over the saved pipeline artifacts on disk.",
        interview_explanation="The monitoring UI is a lightweight FastAPI app that reads saved artifacts and renders teaching-oriented views with Jinja2.",
        why_it_matters="It gives a clear audit trail of who does what at each stage without changing pipeline state.",
    ),
}
