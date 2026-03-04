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

python -m job_coach.main
Overview

AI-powered Job Application Tracker is a production-style backend application that combines traditional application tracking with a Retrieval-Augmented Generation (RAG) pipeline.

The system allows users to:

Track job applications

Upload resumes (PDF)

Automatically index documents using embeddings

Perform resume-to-job matching

Run skill gap analysis

Query their data using a RAG-based assistant

The project demonstrates end-to-end AI engineering practices including document ingestion, vector search, LLM integration, evaluation, and containerized multi-service architecture.

Architecture

The system is built as a multi-service application:

FastAPI — API layer

PostgreSQL — relational data storage

Qdrant — vector database for embeddings

Ollama — local LLM inference

Redis — caching layer

Celery — background task processing

High-Level Flow

User uploads resume or job description

Document is parsed and chunked

Chunks are converted to embeddings

Embeddings are stored in Qdrant with metadata

User query triggers:

Retrieval (vector search + optional hybrid search)

Context construction

LLM inference via Ollama

Structured response generation

Core Features
1. Authentication & Job Tracking

JWT-based authentication

CRUD for job applications

Status tracking (Applied, Interview, Offer, Rejected)

2. Document Ingestion Pipeline

PDF parsing (PyMuPDF)

Configurable chunking strategy

Metadata tagging

Background indexing with Celery

3. Embedding & Vector Search

Sentence-transformer embeddings

Qdrant vector storage

Metadata filtering by user

Configurable top-k retrieval

Optional enhancements:

Hybrid search (keyword + vector)

Cross-encoder reranking

4. RAG Pipeline

RAG flow:

User Query
→ Query Processing
→ Vector Retrieval
→ Context Builder
→ Ollama LLM
→ Structured Output

Features:

Configurable prompts

JSON-structured responses (Pydantic validation)

Query rewriting (optional)

Reranking (optional)

5. Skill Gap Analysis

Structured extraction of skills from resume and job descriptions

Intersection and missing skill detection

Match score calculation

JSON-based response format

6. Evaluation Layer

Retrieval precision@k

Latency tracking

Query + retrieved document logging

Benchmark script for evaluation

Project Structure
app/
  api/
  core/
  db/
  models/
  schemas/
  services/
  tasks/

ml/
  ingestion/
  embeddings/
  rag/
  analysis/
  evaluation/

docker/
Technology Stack

Backend:

Python

FastAPI

SQLAlchemy

Alembic

AI / ML:

sentence-transformers

LangChain

Ollama

Qdrant

Infrastructure:

Docker

Docker Compose

Redis

Celery

Database:

PostgreSQL

Running the Project
1. Clone the repository
git clone <repo_url>
cd ai-job-tracker
2. Start services
docker-compose up --build

Services started:

API

PostgreSQL

Qdrant

Redis

Ollama

3. Run migrations
alembic upgrade head
4. Access API
http://localhost:8000/docs
Example API Endpoints

POST /auth/register
POST /auth/login

POST /jobs/
GET /jobs/

POST /resume/upload

POST /rag/query

POST /analysis/skill-gap

Evaluation

Evaluation scripts are located in:

ml/evaluation/run_eval.py

Metrics:

Retrieval precision@k

Latency per query

Average response time

Why This Project Matters

This project demonstrates:

End-to-end RAG system design

Vector database integration

LLM orchestration with LangChain

Structured output validation

Evaluation and observability

Multi-container production-style deployment

It is not a demo notebook but a containerized, API-first AI system designed with production principles in mind.

Future Improvements

Hybrid retrieval (BM25 + vector)

Cross-encoder reranking

Model benchmarking

CI/CD pipeline

Deployment to cloud environment

job_coach_helper/
│
├── src/
│   └── job_coach/
│       │
│       ├── app/
│       │   ├── api/
│       │   │   ├── routes/
│       │   │   │   ├── auth.py
│       │   │   │   ├── jobs.py
│       │   │   │   ├── resume.py
│       │   │   │   ├── rag.py
│       │   │   │   └── analysis.py
│       │   │   └── dependencies.py
│       │   │
│       │   ├── core/
│       │   │   ├── config.py
│       │   │   └── security.py
│       │   │
│       │   ├── db/
│       │   │   ├── models.py
│       │   │   ├── session.py
│       │   │   └── migrations/
│       │   │
│       │   ├── schemas/
│       │   ├── services/
│       │   ├── tasks/
│       │   └── main.py
│       │
│       ├── ml/
│       │   ├── ingestion/
│       │   ├── embeddings/
│       │   ├── rag/
│       │   ├── analysis/
│       │   └── evaluation/
│       │
│       └── __init__.py
│
├── tests/
├── docker/
├── pyproject.toml
├── Dockerfile
└── README.md

             ┌──────────────────┐
             │      User        │
             └───────┬──────────┘
                     │ HTTP Requests (API)
                     ▼
             ┌──────────────────┐
             │     FastAPI       │
             │    (app/api)      │
             └───────┬──────────┘
      ┌──────────────┼───────────────┐
      │              │               │
      ▼              ▼               ▼
 ┌─────────┐   ┌─────────────┐   ┌────────────┐
 │ Auth &  │   │ Job Tracking│   │ Resume /   │
 │ Users   │   │ CRUD        │   │ Job Parsing│
 └─────────┘   └─────────────┘   └───────┬────┘
                                         │
                                         ▼
                                  ┌─────────────┐
                                  │ Document    │
                                  │ Chunking &  │
                                  │ Metadata    │
                                  └───────┬─────┘
                                          │
                                          ▼
                                  ┌─────────────┐
                                  │ Embeddings  │
                                  │ (sentence-  │
                                  │ transformers)│
                                  └───────┬─────┘
                                          │
                                          ▼
                                  ┌─────────────┐
                                  │ Qdrant      │
                                  │ (Vector DB) │
                                  └───────┬─────┘
                                          │
           ┌──────────────────────────────┼─────────────────────────────┐
           │                              │                             │
           ▼                              ▼                             ▼
 ┌─────────────────┐            ┌──────────────────┐         ┌─────────────────┐
 │ RAG Query Flow   │            │ Skill Gap Analysis│         │ Evaluation      │
 │ 1. Query        │            │ 1. Extract skills │         │ Precision@k     │
 │ 2. Vector Search│            │ 2. Compare        │         │ Latency         │
 │ 3. Context Build│            │ 3. Gap Analysis   │         │ Response logs   │
 │ 4. Ollama LLM   │            └──────────────────┘         └─────────────────┘
 │ 5. Structured   │
 │    Output (JSON)│
 └───────┬─────────┘
         │
         ▼
     ┌───────────┐
     │  User     │
     │ Response  │
     └───────────┘