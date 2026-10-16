# Adaptive RAG — Agentic Document Q&A with Adaptive Query Routing

A full-stack Retrieval-Augmented Generation (RAG) system that answers natural-language questions over uploaded PDFs. A **confidence-based router** sends each query down the best path: **vector retrieval over private documents**, **live web search**, or **direct LLM inference**. Answers are protected by guardrails, LLM-based relevance grading and basic prompt-injection guarding.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript (strict), Vite 5, Tailwind CSS 3 (+ Typography), react-markdown + remark-gfm (GFM rendering), lucide-react |
| **Backend API** | Python 3.12, FastAPI, Uvicorn (ASGI), Pydantic models, python-multipart, CORS middleware |
| **Embeddings** | Sentence-Transformers `all-MiniLM-L6-v2` (384-dim dense vectors), batch encoding |
| **Vector Database** | Qdrant (HNSW index, cosine similarity, payload filtering by source document) |
| **LLM Inference** | Groq API (low-latency LPU inference), `openai/gpt-oss-20b` |
| **Web Retrieval** | Tavily Search API (LLM-optimized real-time web search) |
| **Document Parsing** | pypdf (page-wise text extraction) |

---

## Architecture

```
React SPA (Vite dev proxy /api → :8000)
      │  multipart/form-data            JSON
      ▼                                  ▼
 POST /upload                       POST /ask        GET /documents   GET /health
      │                                  │
 validate (type, ≤5 MB) ─► pypdf ─►      ├─► Guardrails: query validation (empty / >500 chars → rejected)
 sliding-window chunking                 │
 (1000 chars, 150 overlap) ─►            ├─► Router: top-1 cosine score from Qdrant
 batch embed (MiniLM) ─►                 │      ├─ score > 0.35          → RAG
 Qdrant upsert {text, source}            │      ├─ scoped & low score    → "not found in source"
                                         │      └─ else LLM classifier   → WEB | DIRECT
                                         │
                                         ├─► RAG:    top-k=3 retrieval → score threshold (0.25)
                                         │           → LLM relevance grader (CRAG-style) → grounded answer
                                         ├─► WEB:    Tavily top-3 → context-grounded answer + URLs
                                         └─► DIRECT: LLM general-knowledge answer
                                                     (retrieved/web context wrapped with an injection-guard prefix)
```

---

## Key Technical Features

- **Adaptive / agentic routing.** The router scores retrieval confidence first (vector similarity) and only falls back to an **LLM zero-shot classifier** (`web` vs `direct`) when the documents can't answer. This saves LLM calls and reduces hallucination.
- **Corrective RAG (CRAG) pattern.** Retrieved chunks pass a **two-stage filter**: a cosine-similarity threshold, then an **LLM-as-judge relevance grader**. Only graded chunks reach the generation prompt and the citation list.
- **Metadata-filtered semantic search.** Queries can be scoped to a single document through Qdrant payload filters (`FieldCondition` on `source`).
- **Ingestion pipeline.** It validates the file type and size and sanitizes the filename (blocks path traversal), extracts text, uses **overlapping fixed-size chunking** to keep context across chunk boundaries, then **batch-embeds** and upserts all chunks in a single request.
- **Guardrails.** Input validation (length and emptiness) and basic prompt-injection guarding: retrieved and web context is prefixed with an instruction to treat it as reference data and ignore any instructions inside it.
- **Source attribution.** Answers return citations: document chunks with similarity scores and filenames, or web URLs.
- **Non-blocking API.** Model-bound endpoints run as sync handlers in FastAPI's threadpool, so CPU-heavy embedding and blocking network I/O don't stall the event loop.
- **Frontend UX.** Chat interface with drag-and-drop PDF upload (client-side validation that mirrors the server limits), per-document query scoping, colour-coded **route badges** (RAG / Web / General / Rejected), collapsible source citations with similarity scores, Markdown/GFM answer rendering, latency display, backend health monitoring, auto-resizing input with a character limit, and a responsive mobile drawer layout.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload` | Upload a PDF (`multipart/form-data`). Returns `filename`, `characters_extracted`, `chunks_stored` |
| `POST` | `/ask` | `{ query, source? }` → `{ answer, route: rag\|web\|direct\|rejected, sources[] }` |
| `GET` | `/documents` | Lists indexed documents with chunk counts (paginated Qdrant `scroll`) |
| `GET` | `/health` | Liveness check |

---

## Running Locally

```bash
# 1. Vector DB
docker run -p 6333:6333 qdrant/qdrant

# 2. Backend  (copy .env.example → .env and add GROQ_API_KEY, TAVILY_API_KEY)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload          # http://localhost:8000

# 3. Frontend
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

