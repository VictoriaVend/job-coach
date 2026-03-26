# AI-Powered Job Coach

Backend showcase for tracking job applications and demonstrating an end-to-end AI workflow:

- JWT auth and user-scoped CRUD for job applications
- Resume PDF upload with secure file validation
- Background indexing with Celery
- Semantic retrieval with Qdrant
- RAG answers backed by Hugging Face Inference API

This repository is intentionally optimized as an interview-ready backend artifact: reproducible locally with Docker Compose, honest about what is real vs optional, and easy to demo in under 10 minutes.

## What This Project Demonstrates

- FastAPI application design with SQLAlchemy 2.0 and Alembic
- Authenticated multi-tenant API behavior with cross-user isolation
- Background processing using Celery and Redis
- Retrieval-Augmented Generation over uploaded resumes
- Practical engineering hygiene: tests, linting, Docker, CI, and explicit failure modes

## Architecture

```text
Client / Swagger UI
        |
        v
    FastAPI API
      |    | \
      |    |  \-- analysis endpoints (skill gap, semantic match)
      |    |
      |    \---- resume upload -> Celery task -> parsing/chunking/embedding
      |
      +---- PostgreSQL (users, jobs, resumes)
      +---- Redis (Celery broker/result backend)
      +---- Qdrant (vector search)
      \---- Hugging Face Inference API (RAG generation)
```

## Official Showcase Run Path

The main supported demo path is Docker Compose.

### 1. Prepare environment

```bash
cp .env.example .env
```

Required:

- Set `SECRET_KEY` to a real 32+ char secret
- Set `HUGGINGFACEHUB_API_TOKEN` if you want real RAG responses

### 2. Build and start the stack

```bash
docker compose up --build -d
```

This starts:

- `api`
- `celery_worker`
- `postgres`
- `redis`
- `qdrant`

### 3. Apply migrations

```bash
docker compose exec api alembic upgrade head
```

### 4. Open the API docs

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: [http://localhost:8000/health](http://localhost:8000/health)
- Readiness: [http://localhost:8000/ready](http://localhost:8000/ready)

## 10-Minute Demo Flow

1. Register a user via `POST /auth/register`
2. Login via `POST /auth/login`
3. Authorize in Swagger with the returned bearer token
4. Create a job via `POST /jobs/`
5. Upload a resume PDF via `POST /resume/upload`
6. Inspect indexing state via `GET /resume/` or `GET /resume/{id}`
7. Ask a question via `POST /rag/query`
8. Run `POST /analysis/skill-gap` and `POST /analysis/semantic-match`

The showcase story is strongest when you show:

- User isolation in CRUD endpoints
- Resume status lifecycle (`PENDING -> PROCESSING -> COMPLETED/FAILED`)
- Background worker logs during indexing
- RAG responses with retrieved source metadata

## API Surface

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| POST | `/auth/register` | No | Create user |
| POST | `/auth/login` | No | Returns bearer token |
| POST | `/jobs/` | Yes | Create job application |
| GET | `/jobs/` | Yes | List current user's jobs |
| GET | `/jobs/{id}` | Yes | Read one job |
| PATCH | `/jobs/{id}` | Yes | Update one job |
| DELETE | `/jobs/{id}` | Yes | Delete one job |
| POST | `/resume/upload` | Yes | Upload a PDF and queue indexing |
| GET | `/resume/` | Yes | List current user's resumes |
| GET | `/resume/{id}` | Yes | Inspect one resume and indexing status |
| POST | `/analysis/skill-gap` | Yes | Keyword-style gap analysis |
| POST | `/analysis/semantic-match` | Yes | Embedding-based semantic comparison |
| POST | `/rag/query` | Yes | Retrieve from Qdrant and generate answer |
| GET | `/health` | No | Basic service health |
| GET | `/ready` | No | DB readiness check |

## RAG Contract

`POST /rag/query` returns:

```json
{
  "query": "What backend strengths are visible in my resume?",
  "answer": "You show strong Python and FastAPI experience...",
  "sources": [
    {
      "text": "Built FastAPI services and deployed Docker workloads...",
      "score": 0.91,
      "document_id": 12,
      "document_type": "resume",
      "chunk_index": 0
    }
  ]
}
```

If the stack is not configured for real inference, the API fails explicitly with a `503` instead of silently pretending to succeed.

## Resume Status Lifecycle

After upload, a resume moves through these states:

- `PENDING`: metadata stored, task queued
- `PROCESSING`: Celery worker is parsing/chunking/indexing
- `COMPLETED`: raw text saved and vectors indexed
- `FAILED`: background indexing raised an error

## Smoke Check Commands

After the stack is up, these commands verify the happy path quickly:

```bash
docker compose ps
docker compose exec api alembic upgrade head
docker compose logs celery_worker --tail=50
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## Local Development Without Docker

Docker Compose is the official showcase path, but local host development also works if you already have the services available.

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -U pip
pip install -e .[dev,ml,infra]
alembic upgrade head
uvicorn job_coach.app.main:app --reload
```

When running outside Docker, update `DATABASE_URL`, `REDIS_URL`, and `QDRANT_URL` in `.env` accordingly.

## Testing

```bash
pytest
ruff check .
black --check .
```

Tests use SQLite in memory and mock external AI calls where appropriate so the suite stays fast and deterministic.

## What Is Real vs Fallback

Real in this showcase:

- Auth, CRUD, DB persistence, migrations
- Resume file validation and persistence
- Celery task orchestration
- Qdrant-backed retrieval
- Hugging Face-backed RAG when configured

Fallback / explicit failure behavior:

- If ML libraries are missing, AI endpoints return `503`
- If `HUGGINGFACEHUB_API_TOKEN` is missing, RAG returns `503` with a configuration message
- Tests mock external model calls rather than hitting live services

## What I Would Do Next In Production

- Add stronger readiness checks for Redis, Qdrant, and Celery worker liveness
- Introduce typed domain error models across all endpoints
- Move uploads to object storage instead of local disk
- Add rate limiting, audit logs, and stricter auth/session controls
- Add deployment manifests and runtime metrics/tracing

## License

MIT
