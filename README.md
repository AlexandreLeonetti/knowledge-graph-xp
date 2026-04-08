# kg_pdf_mvp

Small local MVP for learning PDF-to-knowledge-graph ingestion with DeepSeek, Neo4j, and PyVis.

This project is intentionally simple. It extracts text from a PDF, chunks it, asks the model for entities and relations as JSON, stores the graph in Neo4j, and generates an interactive HTML visualization.

It does not include embeddings, hybrid retrieval, reranking, or production GraphRAG patterns.

## Project layout

```text
kg_pdf_mvp/
  .env.example
  requirements.txt
  README.md
  data/input/
  data/extracted/
  data/output/
  prompts/extract_graph.txt
  src/config.py
  src/models.py
  src/pdf_loader.py
  src/chunker.py
  src/extractor.py
  src/normalize.py
  src/neo4j_store.py
  src/visualize.py
  src/main.py
```

## 1. Create and activate a virtual environment

From the `kg_pdf_mvp` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure environment variables

Copy the example file:

```bash
cp .env.example .env
```

Fill in:

- `DEEPSEEK_API_KEY`
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`

Optional knobs:

- `DEEPSEEK_BASE_URL` defaults to `https://api.deepseek.com`
- `DEEPSEEK_MODEL` defaults to `deepseek-chat`
- `CHUNK_SIZE` defaults to `1200`
- `CHUNK_OVERLAP` defaults to `150`
- `MAX_CHUNKS` can be set to a small number like `5` to control API cost during learning

## 4. Start Neo4j locally

One straightforward local option is Neo4j Desktop:

1. Install Neo4j Desktop from the official Neo4j website.
2. Create a local DBMS.
3. Set a password for the `neo4j` user.
4. Start the DBMS.
5. Use `bolt://localhost:7687` as `NEO4J_URI`.

If you already have Neo4j installed another way, just make sure Bolt is reachable and the credentials in `.env` match.

## 5. Put a sample PDF in `data/input`

Example:

```bash
cp /path/to/your.pdf data/input/sample.pdf
```

## 6. Run ingestion

```bash
python src/main.py ingest data/input/sample.pdf
```

This will:

- extract PDF text page by page
- build overlapping chunks
- call DeepSeek for each chunk
- write intermediate files under `data/extracted/`
- insert entities and relations into Neo4j
- generate `data/output/graph.html`

Generated artifacts:

- `data/extracted/chunks.json`
- `data/extracted/raw_extractions.json`
- `data/extracted/entities.json`
- `data/extracted/relations.json`
- `data/output/graph.html`

## 7. Rebuild the HTML visualization

```bash
python src/main.py visualize
```

This reads `entities.json` and `relations.json` and rewrites `data/output/graph.html`.

## 8. Run a sample query

Default query:

```bash
python src/main.py query
```

Custom Cypher query:

```bash
python src/main.py query "MATCH (a:Entity)-[r:RELATED]->(b:Entity) RETURN a.name AS source, r.type AS relation, b.name AS target LIMIT 10"
```

Example Cypher query for Neo4j Browser:

```cypher
MATCH (a:Entity)-[r:RELATED]->(b:Entity)
RETURN a.name AS source, r.type AS relation, b.name AS target, r.chunk_id AS chunk_id
LIMIT 25
```

## Notes

- Start with a small PDF or set `MAX_CHUNKS=3` or `MAX_CHUNKS=5` to keep token usage low while learning.
- The model is instructed to only extract facts explicitly supported by each chunk, but LLM output can still be imperfect.
- `visualize` uses the saved JSON artifacts, which makes it easy to inspect or tweak outputs without calling the API again.
- This MVP is intentionally minimal and does not yet include embeddings, vector search, hybrid retrieval, or any production hardening.
