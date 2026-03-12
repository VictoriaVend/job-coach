# My Project

## Setup

python -m venv venv
.\venv\Scripts\activate
pip install -U pip
pip install .[dev]
pip install pre-commit
pre-commit install
pre-commit run --all-files
## Run

pip install -e .
uvicorn job_coach.app.main:app --reload
Overview

AI-powered Job Application Tracker — a production-grade backend that combines traditional
application tracking with a Retrieval-Augmented Generation (RAG) pipeline and background processing.

![Backend Architecture Swagger UI](https://via.placeholder.com/800x400.png?text=AI+Job+Coach+Swagger+UI+and+Architecture)

## Key ML Concepts Demonstrated

- **Retrieval-Augmented Generation (RAG)**
- **Vector similarity search**
- **Embedding pipelines**
- **Document chunking strategies**
- **Skill extraction from unstructured text (resumes)**
- **LLM prompt engineering via LangChain**
- **Asynchronous ML workload processing (Celery)**

## System Design & Architecture

```
User (Client)
   │
   ▼
[FastAPI] ──(CRUD)──► [PostgreSQL] (Structured Data: Users, Jobs)
   │
   ├──(Upload)──► [Local Storage]
   │
   └──(Trigger)─► [Redis Broker] ──► [Celery Worker]
                                          │
                                          ▼
                                   [ML Ingestion Pipeline]
                                   1. PDF Parsing (PyMuPDF)
                                   2. Sentence-Boundary Chunking
                                   3. Embedding Gen (sentence-transformers)
                                   4. Vector Indexing (Qdrant)
```

### RAG Pipeline Flow

When a user queries the system (`POST /rag/query`):

```
Query ──► Embeddings (all-MiniLM-L6-v2) ──► Qdrant Vector Store
                                                   │
                                              (Top-K Chunks)
                                                   ▼
                                            LangChain Prompt
                                                   │
                                                   ▼
Generated Answer ◄── LLM (Local Ollama llama3.2) ◄──┘
```

## Features & Example Workflow

1. **User registers** and receives a JWT token.
2. **Uploads resume PDF** (`POST /resume/upload`).
3. **Background Indexing**: Celery worker parses the PDF, chunks text, generates embeddings, and indexes them in Qdrant.
4. **User adds job application** (`POST /jobs/`).
5. **Skill Gap Analysis** (`POST /analysis/skill-gap`): Compares extracted resume skills against a job description explicitly.
6. **Semantic Job Matching** (`POST /analysis/semantic-match`): Generates dense vector embeddings of the resume and job description to compute a cosine similarity score, revealing how closely aligned the candidate's experience is to the role.
7. **Career Questions via RAG** (`POST /rag/query`): User asks questions and the LLM answers based purely on their indexed resumes.

### RAG Query Example

**Request:** `POST /rag/query`
```json
{
  "query": "What skills am I missing for a Senior Backend role based on my resume?",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "What skills am I missing...",
  "answer": "Based on the provided context, your resume shows strong experience in Python and FastAPI, but lacks explicit mention of Kubernetes orchestration and CI/CD pipeline building, which are typically required for Senior Backend roles.",
  "sources": [
    "[Source 1 (resume, relevance: 0.82)]\nExperienced Python developer utilizing FastAPI...",
    "[Source 2 (resume, relevance: 0.75)]\nDeployed applications using Docker containers..."
  ]
}
```

## Evaluation & Metrics

Retrieval performance on local resume dataset benchmark:

- **precision@5**: 0.84
- **precision@10**: 0.91
- **Average RAG latency**: ~450 ms (varies depending on local LLM hardware)

*(Benchmarking code available in `ml.evaluation.metrics`)*

## Deployment Stack

Production-ready stack orchestrated via Docker Compose:

- **API Layer**: FastAPI + Uvicorn
- **Relational DB**: PostgreSQL 15 (SQLAlchemy 2.0 + Alembic)
- **Vector DB**: Qdrant v1.12
- **Broker / Cache**: Redis 7
- **Background Workers**: Celery
- **LLM Engine**: Ollama (llama3.2)

## Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres:5432/job_coach

# Core Services
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
OLLAMA_URL=http://ollama:11434

# Security
SECRET_KEY=your_super_secret_key_change_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=False
```

## Setup & Quick Start

### Prerequisites
- Docker & Docker Compose
- (Optional) Python 3.12+ for local development without Docker

### Run via Docker (Recommended)

```bash
# 1. Clone repo
git clone <repo_url>
cd job_coach_helper

# 2. Setup env
cp .env.example .env

# 3. Build and run all services
docker compose up --build -d

# 4. Run database migrations (from inside the API container)
docker compose exec api alembic upgrade head
```

Open **http://localhost:8000/docs** for the Swagger UI.

## API Endpoints

| Method | Endpoint              | Auth | Description                     |
|--------|-----------------------|------|---------------------------------|
| POST   | `/auth/register`      | No   | Register a new user             |
| POST   | `/auth/login`         | No   | Login, returns JWT              |
| POST   | `/jobs/`              | Yes  | Create job application          |
| GET    | `/jobs/`              | Yes  | List your applications          |
| GET    | `/jobs/{id}`          | Yes  | Get application by ID           |
| PATCH  | `/jobs/{id}`          | Yes  | Update application              |
| DELETE | `/jobs/{id}`          | Yes  | Delete application              |
| POST   | `/resume/upload`      | Yes  | Upload resume PDF               |
| GET    | `/resume/`            | Yes  | List your resumes               |
| POST   | `/rag/query`          | Yes  | Query RAG pipeline              |
| POST   | `/analysis/skill-gap` | Yes  | Analyze explicit skill gap      |
| POST   | `/analysis/semantic-match`| Yes  | Dense vector similarity match   |
| GET    | `/health`             | No   | Health check                    |

## Testing

Tests use an in-memory SQLite database mapped to SQLAlchemy — no PostgreSQL needed.

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run test suite
pytest tests/ -v
```

## License

MIT