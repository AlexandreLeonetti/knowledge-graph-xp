Here's the full map, ranked from absolutely must-know to nice-to-have bonus. I've organized them into tiers.

---

## 🔴 TIER 1 — Must Know Cold (You'll be asked directly)

**1. Embeddings & Vector Search**
Dense vector representations of text. The foundation of semantic retrieval. Know the difference between embedding models (OpenAI `text-embedding-3`, BGE, E5).

**2. Chunking Strategies**
Key methods: fixed-length, sentence-based, paragraph-based, semantic chunking (meaning-based), sliding window (overlapping chunks to preserve context), and late chunking (chunking after embedding, using full-document context). You need to explain tradeoffs between all of these.

**3. Hybrid Search (BM25 + Dense)**
Hybrid retrieval combines BM25 keyword precision with dense semantic embeddings. BM25 dominates for exact terms like product codes; vector search excels at conceptual queries. Scores are fused using weighted averages or Reciprocal Rank Fusion (RRF).

**4. Reranking**
After an initial retrieval pass, reranking models more precisely evaluate relevance, selecting only the most contextually relevant documents before generation — significantly reducing noise and hallucinations. Know Cohere Rerank, cross-encoders vs bi-encoders.

**5. Vector Databases**
Pinecone, Weaviate, Qdrant, pgvector, Chroma. Know approximate nearest neighbor (ANN), HNSW indexing, and metadata filtering.

**6. Hallucination & Grounding**
RAG's core value prop. Know the RAG Triad: context relevance (does retrieved content match the query?), groundedness (is the answer backed by retrieved evidence?), and answer relevance (does the final answer address the question?).

---

## 🟠 TIER 2 — Expected from a Senior Engineer

**7. Knowledge Graphs / Graph RAG**
GraphRAG (Microsoft) — entities and relationships indexed as graphs rather than flat chunks. Enables multi-hop reasoning. Contrast with vector RAG: graphs preserve relationships, vectors preserve semantic similarity.

**8. Agentic RAG**
Hierarchical Agentic RAG organizes agents in a hierarchy, with higher-level agents overseeing lower-level agents, enabling multi-level decision-making so queries are handled by the most appropriate resources. The LLM decides *when* to retrieve and *what* to retrieve.

**9. Query Transformation**
HyDE (Hypothetical Document Embeddings), query expansion, step-back prompting, sub-query decomposition. Transforms the raw user query before retrieval to improve recall.

**10. Metadata Filtering**
Robust metadata filtering allows for highly specific context windowing — querying only documents matching specific criteria (date, source, department) dramatically reduces noise.

**11. Indexing Strategies**
Parent-child chunking, hierarchical indexing, RAPTOR. RAPTOR uses recursive abstractive processing with tree-organized retrieval, generating hierarchical structures from 100-token leaf nodes up to high-level conceptual root nodes through clustered intermediate summaries.

**12. RAG Evaluation Frameworks**
RAGAS, TruLens, LangSmith. Know how to measure retrieval recall, answer relevancy, faithfulness. This is production-critical.

**13. MCP (Model Context Protocol)**
Anthropic's open protocol for connecting LLMs to external tools and data sources at inference time. Increasingly standard in agentic pipelines — know what it is and how it differs from function calling.

---

## 🟡 TIER 3 — Differentiators (Sets You Apart)

**14. Reciprocal Rank Fusion (RRF)**
The standard score fusion algorithm when combining sparse + dense retrieval results. Simple but effective — interviewers love it.

**15. Contextual Compression**
Extracting only the relevant portion of a retrieved chunk before feeding it to the LLM. Reduces context window noise.

**16. Multimodal RAG**
Multimodal RAG integrates image, audio, tabular, and video embeddings to create more holistic reasoning — a core trend in enterprise RAG through 2025–26.

**17. Late Interaction Models (ColBERT)**
Token-level late interaction between query and document. More accurate than bi-encoders, cheaper than cross-encoders. Know where it fits.

**18. Streaming RAG & Caching**
Advanced caching significantly reduces latency and API costs for repetitive queries — important for production systems.

**19. Feedback Loops & Continuous Improvement**
Logging user interactions, collecting ratings, and tracking errors highlights where the system fails. This data can be used to retrain retrievers, adjust selection heuristics, or improve prompt formats.

**20. Long-Context vs RAG Tradeoffs**
With models like Gemini 1.5 at 1M tokens, interviewers may ask: "Why RAG over just stuffing everything in context?" Know the cost, latency, relevance, and privacy arguments.

---

## 🟢 TIER 4 — Bonus / Research-Level

- **HyperGraph Memory (HGMem)** — multi-step RAG with hypergraph-based memory
- **Self-RAG** — model learns to decide when to retrieve
- **Corrective RAG (CRAG)** — evaluates retrieval quality and self-corrects
- **FLARE** — forward-looking active retrieval (retrieves mid-generation)
- **DeR2 / Reasoning-Retrieval decoupling** — separating reasoning failures from retrieval failures in evaluation

---

Given your background with the Renault and Sanofi RAG pipelines, you're already battle-tested on tiers 1 and 2. The sharpest differentiator for your interviews right now is being able to speak fluently about **Graph RAG vs Vector RAG**, **agentic retrieval**, and **evaluation frameworks** — that's what separates "built a RAG" from "senior RAG engineer."





Good catch — evals is actually a huge topic on its own and very likely to come up in senior interviews. Here's the full breakdown:

---

## RAG Evals — Keywords Ranked by Interview Importance

---

### 🔴 TIER 1 — Core Metrics (You Must Know These Cold)

**1. Faithfulness**
Is the generated answer factually consistent with the retrieved context? This is the anti-hallucination metric. Score = 0 means the model made things up.

**2. Answer Relevancy**
Does the answer actually address the user's question? A high faithfulness + low answer relevancy means the model answered something else correctly.

**3. Context Precision**
Of all the chunks retrieved, how many were actually relevant? Measures retrieval noise.

**4. Context Recall**
Did the retrieval surface all the chunks needed to answer the question? Measures retrieval completeness.

These four are the **RAGAS core metrics** — they evaluate different dimensions without relying on ground truth human annotations, which is what makes RAGAS powerful in practice.

**5. Groundedness (RAG Triad)**
Groundedness evaluates whether generated responses are adequately substantiated by the retrieved evidence. TruLens' version of faithfulness — same concept, different framing.

---

### 🟠 TIER 2 — Frameworks (Must Know What Each Is For)

**6. RAGAS**
The most widely adopted open-source RAG evaluation framework, grown from a 2023 research paper on reference-free evaluation. It's become the de facto standard for the core metrics. Use it for metric exploration and synthetic dataset generation.

**7. DeepEval**
The strongest choice for blocking bad deployments. It integrates with pytest and is designed for CI/CD quality gates with pass/fail thresholds. Think of it as "pytest for LLMs."

**8. TruLens**
Most useful during the experimentation phase when comparing different chunking strategies, embedding models, or retrieval configurations, with metric scores visible per run in a dashboard.

**9. LangSmith / Langfuse**
Production monitoring and tracing tools. Used for real-time tracking of user experience and catching drift in production. Know the difference: LangSmith is LangChain-native, Langfuse is framework-agnostic and self-hostable.

**10. The recommended production stack**
This is a question interviewers love to ask. The answer: RAGAS for metric design, DeepEval for CI/CD quality gates, and TruLens or Langfuse for ongoing production monitoring.

---

### 🟡 TIER 3 — Concepts & Patterns

**11. LLM-as-Judge**
Using an LLM (GPT-4, Claude) to score another LLM's output. The standard approach for reference-free evaluation. Know its bias risks (models favor their own outputs) and mitigation strategies.

**12. Golden Dataset / Test Set**
A curated set of 50–200 question-answer pairs covering domain edge cases. Run against on every PR. Target thresholds: context precision > 0.8, faithfulness > 0.8, answer relevancy > 0.75.

**13. Synthetic Data Generation for Evals**
Since labeling evaluation data is expensive, RAGAS and DeepEval can auto-generate QA pairs from your document corpus. Critical for bootstrapping evals on a new domain.

**14. CI/CD Eval Integration**
The goal is simple: fail the build when RAG quality drops below your thresholds before a PR gets merged. Wire DeepEval to GitHub Actions — this is what separates a junior RAG builder from a senior one.

**15. Retrieval vs Generation failure modes**
Know how to diagnose *where* the pipeline broke. Low context recall = retrieval problem. Low faithfulness with high context precision = generation problem. This diagnostic framing is what interviewers want to hear.

---

### 🟢 TIER 4 — Bonus / Advanced

**16. Arize Phoenix**
OpenTelemetry-based observability — traces embedding clusters and latency. Good for visual debugging of retrieval in production.

**17. Noise Sensitivity**
A newer RAGAS metric — how much does the answer quality degrade when irrelevant chunks are mixed in with relevant ones?

**18. ARES (Automated RAG Evaluation System)**
Stanford research-grade framework. Know it exists; not expected in standard interviews.

**19. Continuous / Online Evaluation**
Moving beyond offline test sets to evaluating live traffic samples. Ties into feedback loops, user ratings, and production drift detection.

---

### The Mental Model to Pitch in an Interview

Frame it in 3 layers:
- **Offline** (pre-deploy): golden dataset + RAGAS + DeepEval blocking merges
- **Staging**: batch evaluation per release
- **Production**: LangSmith/Langfuse tracing + real-time faithfulness monitoring

This shows you think about evals as an engineering discipline, not just a metric you run once.
