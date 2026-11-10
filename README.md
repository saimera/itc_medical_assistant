# Medical RAG App

A Retrieval-Augmented Generation (RAG) chatbot that answers questions about a medical center's [PlacidWay](https://www.placidway.com) profile (ITC Immunity Therapy Center). Answers are grounded in the scraped source content and returned with source citations.

> **Disclaimer:** Responses reflect claims made by the source profile. They are not verified medical facts and are not medical advice.

## Features

- End-to-end pipeline: scrape, clean, chunk, embed, retrieve and generate
- Token-aware chunking with overlap and per-chunk title/type context
- Semantic search via Pinecone integrated embeddings
- PostgreSQL as the source of truth for documents and chunks, with Alembic migrations
- Answers constrained to retrieved context, with source URLs
- FastAPI backend with a lightweight web chat UI

## Architecture

```
PlacidWay page
     │  scrape.py
     ▼
JSON records ──► prepare_corpus.py ──► markdown.py ──► load_documents.py
                                                              │
                                                              ▼
                                                    PostgreSQL (documents)
                                                              │  chunking.py
                                                              ▼
                                                    PostgreSQL (chunks)
                                                              │  vectorize.py
                                                              ▼
                                                    Pinecone (vector index)

Query ──► FastAPI /chat ──► Pinecone search ──► PostgreSQL lookup ──► Groq LLM ──► Answer + sources
```

## Tech Stack

| Layer      | Technology                                   |
|------------|----------------------------------------------|
| API        | FastAPI, Uvicorn                             |
| Database   | PostgreSQL, SQLAlchemy, Alembic              |
| Vector DB  | Pinecone                                     |
| LLM        | Groq (`openai/gpt-oss-120b`)                 |
| Scraping   | Requests, BeautifulSoup                      |
| Tokenizer  | Hugging Face `tokenizers`                    |
| Tooling    | Python 3.14+, [uv](https://docs.astral.sh/uv/) |

## Prerequisites

- Python 3.14+ and `uv`
- A PostgreSQL database
- A [Pinecone](https://www.pinecone.io) account with an index named `medical-rag-chunks`, configured with an integrated embedding model that maps `chunk_text` as the text field
- A [Groq](https://console.groq.com) API key

## Setup

```bash
git clone https://github.com/saimera/medical_rag_app.git
cd medical_rag_app
uv sync
```

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/medical_rag
PINECONE_API_KEY=your-pinecone-key
GROQ_API_KEY=your-groq-key
```

Apply database migrations:

```bash
uv run alembic upgrade head
```

## Data Pipeline

Run once from the project root, in order. Generated files are written to `data/` (git-ignored).

```bash
uv run python -m app.medical_rag.scrape                  # 1. Scrape and parse the profile page
uv run python -m app.medical_rag.prepare_corpus          # 2. Normalize records into one corpus
uv run python -m app.medical_rag.ingestion.markdown      # 3. Convert corpus to Markdown
uv run python -m app.medical_rag.ingestion.load_documents  # 4. Load document into PostgreSQL
uv run python -m app.medical_rag.scripts.chunking        # 5. Split into overlapping chunks
uv run python -m app.medical_rag.scripts.vectorize       # 6. Upsert chunks to Pinecone
```

## Run the App

```bash
uv run uvicorn app.medical_rag.routes.medical_rag:app --reload
```

Open [http://localhost:8000](http://localhost:8000) to use the chat UI.

## API

| Method | Endpoint  | Description                          |
|--------|-----------|--------------------------------------|
| GET    | `/`       | Chat UI                              |
| GET    | `/health` | Health check                         |
| POST   | `/chat`   | Ask a question, get answer + sources |

**Example**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What treatments does ITC offer?"}'
```

```json
{
  "answer": "...",
  "sources": ["https://www.placidway.com/profile/5/..."]
}
```

Interactive API docs are available at `/docs`.

## Project Structure

```
├── app/medical_rag/
│   ├── db/            # SQLAlchemy base, session, models (Document, Chunk)
│   ├── ingestion/     # Markdown conversion and document loading
│   ├── routes/        # FastAPI app and chat router
│   ├── scripts/       # Chunking and vectorization
│   ├── scrape.py      # Web scraper
│   └── prepare_corpus.py
├── services/          # Retrieval (query_service) and generation (llm)
├── migrations/        # Alembic migrations
├── static/            # Frontend CSS and JS
└── templates/         # HTML template
```

## Configuration

| Setting         | Location                          | Default                        |
|-----------------|-----------------------------------|--------------------------------|
| Chunk size      | `scripts/chunking.py`             | 300 tokens, 50 overlap         |
| Top-K retrieval | `services/query_service.py`       | 5                              |
| Pinecone index  | `query_service.py`, `vectorize.py`| `medical-rag-chunks`           |
| LLM model       | `services/llm.py`                 | `openai/gpt-oss-120b`          |

## Notes

- The pipeline targets a single source page; change the URL and document ID constants to index other pages.
- Respect the source website's terms of service and robots policy when scraping.

## Author

Saim Maqsood