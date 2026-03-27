from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from job_coach.app.api.routes import analysis, jobs, rag, resume, users
from job_coach.app.core.config import settings
from job_coach.app.core.logger import logger
from job_coach.app.db.session import engine

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Backend API for tracking job applications and AI-powered resume analysis"
    ),
    version=settings.APP_VERSION,
)


# Secure Web Headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Starting AI-powered Job Coach API")

# Auth routes
app.include_router(users.router, prefix="/auth")
# Job application CRUD
app.include_router(jobs.router, prefix="/jobs")
# Resume upload / management
app.include_router(resume.router, prefix="/resume")
# RAG query pipeline
app.include_router(rag.router, prefix="/rag")
# Skill gap analysis
app.include_router(analysis.router, prefix="/analysis")


@app.get("/health", tags=["system"])
def health_check():
    logger.debug("Health check requested")
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "debug": settings.DEBUG,
    }


@app.get("/ready", tags=["system"])
def readiness_check():
    checks = {"database": "ok"}

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning(f"Readiness database check failed: {exc}")
        checks["database"] = "error"
        return {"status": "degraded", "checks": checks}

    return {"status": "ok", "checks": checks}
