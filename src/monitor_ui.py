from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import BASE_DIR
from monitoring_loader import ArtifactLoader


TEMPLATES_DIR = BASE_DIR / "src" / "monitor_templates"
STATIC_DIR = BASE_DIR / "src" / "monitor_static"

app = FastAPI(title="KG PDF Monitor", version="0.1.0")
app.mount("/monitor-static", StaticFiles(directory=STATIC_DIR), name="monitor-static")
app.mount("/lib", StaticFiles(directory=BASE_DIR / "lib"), name="lib")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
loader = ArtifactLoader()


def pretty_json(value) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)


templates.env.filters["pretty_json"] = pretty_json


def render(request: Request, template_name: str, **context):
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=context,
    )


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/monitor", status_code=307)


@app.get("/monitor", response_class=HTMLResponse)
def monitor_home(request: Request):
    return render(
        request,
        "home.html",
        page_title="Pipeline monitor",
        home=loader.build_home_view(),
    )


@app.get("/pdf-extraction", response_class=HTMLResponse)
def pdf_extraction(request: Request):
    chunks = loader.load_chunks()["data"]
    pdf_view = loader.load_pdf_extraction(chunks)
    return render(
        request,
        "pdf_extraction.html",
        page_title="PDF extraction",
        pdf_view=pdf_view,
        stage_info=loader.get_stage_info("pdf-extraction"),
    )


@app.get("/chunks", response_class=HTMLResponse)
def chunk_inspector(request: Request, chunk: int = 1):
    chunks_artifact = loader.load_chunks()
    chunks = chunks_artifact["data"]
    raw_rows = loader.load_raw_extractions()["data"]
    raw_by_chunk = {row["chunk_id"]: row for row in raw_rows}

    selected = None
    selected_index = 0
    if chunks:
        selected_index = min(max(chunk, 1), len(chunks)) - 1
        selected = chunks[selected_index]
        selected["raw_extraction"] = raw_by_chunk.get(selected["id"])

    return render(
        request,
        "chunks.html",
        page_title="Chunk inspector",
        chunks=chunks,
        selected_chunk=selected,
        selected_index=selected_index,
        missing_message=chunks_artifact["error"] or "Chunks are not available yet.",
        stage_info=loader.get_stage_info("chunks"),
    )


@app.get("/raw-extractions", response_class=HTMLResponse)
def raw_extraction_inspector(request: Request, item: int = 1):
    raw_artifact = loader.load_raw_extractions()
    rows = raw_artifact["data"]

    selected = None
    selected_index = 0
    if rows:
        selected_index = min(max(item, 1), len(rows)) - 1
        selected = rows[selected_index]

    return render(
        request,
        "raw_extractions.html",
        page_title="Raw extraction inspector",
        rows=rows,
        selected_row=selected,
        selected_index=selected_index,
        missing_message=raw_artifact["error"] or "Raw extraction records are not available yet.",
        stage_info=loader.get_stage_info("raw-extractions"),
    )


@app.get("/normalization", response_class=HTMLResponse)
def normalization_inspector(request: Request):
    view = loader.build_normalization_view()
    return render(
        request,
        "normalization.html",
        page_title="Normalization inspector",
        view=view,
        stage_info=loader.get_stage_info("normalization"),
    )


@app.get("/graph", response_class=HTMLResponse)
def graph_page(request: Request):
    graph_artifact = loader.load_graph_artifact()
    return render(
        request,
        "graph.html",
        page_title="Graph view",
        graph_artifact=graph_artifact,
        stage_info=loader.get_stage_info("graph"),
    )


@app.get("/graph-artifact", response_class=HTMLResponse)
def graph_artifact():
    html = loader.load_graph_html()
    if html is None:
        raise HTTPException(status_code=404, detail="Graph HTML is not available yet.")
    return HTMLResponse(content=html)
