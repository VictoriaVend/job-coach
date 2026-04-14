# Job Coach Backend - Comprehensive Coding Style Guide

This document outlines the strict coding standards, architectural patterns, and formatting rules used in the `job_coach_helper` project. It serves as a single source of truth for all developers and AI assistants to ensure a consistent, maintainable, secure, and performant codebase.

---

## 1. Project Architecture (Clean Architecture & Hexagonal Concepts)

The codebase strictly separates the **Delivery Mechanism (API)** from the **Business Logic (Services)** and the **Infrastructure/Data Layer**.

*   **`src/job_coach/app/api/routes/` (Controllers / Endpoints)**
    *   **Rule:** MUST be "thin". **No business logic, no complex data transformations, and absolutely no direct file I/O or background task dispatching.**
    *   **Responsibility:** Validate HTTP requests (via Pydantic schemas), call the appropriate `Service` layer method, and return the formatted response.
    *   **Exceptions in Controllers:** Controllers MUST NOT raise raw `HTTPException` directly. Instead, raise domain exceptions from `src/job_coach/app/core/exceptions.py` (e.g., `exc.NotFoundError`, `exc.ValidationError`). *Note: Legacy routes like `rag.py` and `analysis.py` currently use `HTTPException` and need refactoring to use domain exceptions.*
    *   **Dependencies:** Inject DB sessions (`DBSession`) and users (`CurrentUser`) via FastAPI's `Depends()`. Pass these into the service layer. Use `Annotated` for cleaner dependency injection (e.g., `DBSession = Annotated[AsyncSession, Depends(get_db)]`).

*   **`src/job_coach/app/services/` (Business Logic)**
    *   **Rule:** This is where the core application logic lives. Classes should encapsulate specific domain operations (e.g., `ResumeService`, `UserService`).
    *   **Responsibility:** Orchestrate data validation, interact with the database (via SQLAlchemy sessions passed from the router), handle file system operations (safely), and dispatch background tasks (Celery).

*   **`src/job_coach/app/models/` & `src/job_coach/app/schemas/` (Data & Validation)**
    *   **Models (SQLAlchemy 2.0):** Use `Mapped` and `mapped_column` for strict typing. Use `Enum` classes for status fields (e.g., `ResumeStatus`).
    *   **Schemas (Pydantic V2):** Separate schemas for input (`Create`, `Update`) and output (`Read`). Always use `model_config = {"from_attributes": True}` for ORM serialization.

*   **`src/job_coach/ml/` (Machine Learning & AI)**
    *   **Rule:** Must be completely decoupled from the FastAPI web context. Operates via pure function calls or background tasks.
    *   **Responsibility:** Document parsing (`parser.py`), embeddings generation, RAG pipeline execution, and vector database (Qdrant) interactions.

*   **`src/job_coach/app/tasks/` (Background Workers - Celery)**
    *   **Rule:** Because tasks run in separate processes outside the FastAPI request lifecycle, they MUST manage their own database sessions using `async with AsyncSessionLocal() as db:`.
    *   **Error Handling:** Use Celery's retry mechanisms (`self.retry`) with exponential backoff (`countdown=2**self.request.retries`). Only mark database records as `FAILED` after all retries are exhausted. Implement strict cleanup (e.g., deleting orphaned files on permanent failure).

---

## 2. Security & Configuration (`pydantic-settings`)

*   **Config Source of Truth:** `src/job_coach/app/core/config.py`.
*   **Rule (NO HARDCODING):** Never hardcode magic numbers (chunk sizes, file limits), URLs, API keys, or model identifiers in the application code. Read everything from `settings`.
*   **Validation at Startup:** Use `@model_validator(mode="after")` to enforce strict security rules (e.g., the `SECRET_KEY` must not be a placeholder and must be 32+ characters long). The app must crash on startup if security invariants are violated.

---

## 3. Asynchronous Programming & I/O Operations

*   **Async Everywhere:** The project relies heavily on `asyncio`. Use asynchronous drivers (`asyncpg`) for PostgreSQL and asynchronous HTTP clients (`httpx`).
*   **Rule (No Blocking):** Do not mix synchronous blocking calls (like `requests.get` or `time.sleep`) inside `async def` functions.
*   **Memory Management (Streaming):**
    *   **Rule:** NEVER load entire large files (like 50MB PDFs) into memory at once on the web server.
    *   **Action:** Use `await file.read(settings.UPLOAD_CHUNK_SIZE)` to stream files to disk.
*   **Lazy Loading:**
    *   **Rule:** ML models (`sentence-transformers`), large C++ bindings (`PyMuPDF/fitz`), and external clients (`qdrant_client`) should be loaded lazily (inside functions or properties) to reduce application startup time and save RAM if a specific worker process doesn't need them.

---

## 4. Error Handling (`src/job_coach/app/core/exceptions.py`)

We use a centralized, hierarchical exception system to ensure consistent API error responses.

*   **Base Class:** `JobCoachError`.
*   **Rule (No Raw 500s):** NEVER return raw HTTP 500 errors with stack traces to the user.
*   **Rule (No HTTPException in API):** Do not use `raise HTTPException` in route handlers. Instead, raise domain-specific exceptions.
    *   *✅ Good:* `raise exc.NotFoundError("User not found")`
    *   *❌ Bad:* `raise HTTPException(status_code=404, detail="User not found")`
*   **Action:** Raise specific domain exceptions (e.g., `NotFoundError`, `ValidationError`, `PayloadTooLargeError`, `InternalServerError`, `ExternalServiceError`).
*   **Handling:** The global exception handlers in `main.py` catch these and format them into standardized JSON responses with incident IDs.

---

## 5. Logging (`structlog`)

*   **Tool:** `structlog` via `job_coach.app.core.logger`.
*   **Rule (Structured Logging):** Always use native keyword arguments (kwargs) instead of string concatenation, f-strings, or the legacy `extra={}` dictionary for dynamic data. This ensures logs are flattened and easily queryable in production (e.g., Elasticsearch, Loki).
    *   *✅ Good:* `logger.info("Indexing failed", user_id=current_user.id, resume_id=resume.id, attempt=attempt_number)`
    *   *❌ Bad:* `logger.info(f"Indexing failed for resume {resume.id} on attempt {attempt_number}")`
*   **Context:** Include relevant IDs (`user_id`, `resume_id`, `task_id`) in every log message to trace requests across the system.
*   **Audit Logging:** Use `audit_logger` for sensitive security events (login, registration, permission changes).

---

## 6. Formatting, Linting & Typing (Enforced by CI/CD)

We rely on strict automated tooling. All code MUST pass these checks.

*   **Formatter:** Black (`black`)
    *   Line length: **90 characters**.
*   **Linter:** Ruff (`ruff`)
    *   Line length: **120 characters**.
    *   Enabled rules: `E` (pycodestyle errors), `F` (Pyflakes), `I` (isort - automatic import sorting).
*   **Type Checker:** Mypy (`mypy`)
    *   All functions, variables, and class attributes must have type hints.
    *   Use modern Python 3.10+ type hints (`|` instead of `Union`, `list[str]` instead of `List[str]`).
    *   Missing imports from untyped third-party libraries are ignored globally (`ignore_missing_imports = true` in `pyproject.toml`), but try to avoid them.
*   **Pre-commit Hooks:** Enforced via `.pre-commit-config.yaml`. Before committing, run `pre-commit run --all-files`.

---

## 7. Testing Strategy (`pytest`)

*   **Framework:** `pytest` and `pytest-asyncio`.
*   **Mocking Boundaries:** Any operation that touches the network (HuggingFace APIs, Qdrant), reads/writes files, or dispatches external tasks (`Celery.delay()`) **MUST** be mocked using `unittest.mock.patch` in unit tests.
*   **Database Isolation:** Tests interacting with the database must use a test session fixture and rollback after each test to ensure state isolation.

---

## 8. Specific Domain Rules (ML & Ingestion)

*   **Semantic Chunking:** Text chunking must be "Section-Aware". Raw text must be pre-processed to identify language and logical sections (Experience, Education). The section name must be injected into the text of every chunk to preserve context for the Embedding model and LLM (e.g., `[Experience] ...text...`).
*   **Fail-Fast Validation:** Validate file types (Magic Bytes) on the *first streamed chunk* during upload to prevent disk I/O abuse.
*   **Vector DBs (Qdrant):** Ensure payloads and metadata are properly indexed for fast, filtered retrieval.
    *   *Example:*
        ```python
        await client.create_payload_index(
            collection_name="resumes",
            field_name="user_id",
            field_schema="keyword"
        )
        ```
*   **LLM Interactions (HuggingFace/Mistral):** Ensure deterministic outputs where required (e.g., `temperature=0.1`). Always handle external API timeouts and implement retry mechanisms with exponential backoff.
    *   *Example:*
        ```python
        from tenacity import retry, wait_exponential, stop_after_attempt

        @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
        async def call_llm_api(prompt: str):
            ...
        ```
