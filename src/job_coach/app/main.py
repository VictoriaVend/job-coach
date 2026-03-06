from fastapi import FastAPI

from job_coach.app.api.routes import analysis, jobs, rag, resume, users

app = FastAPI(
    title="AI-powered Job Coach",
    description="Backend API for tracking job applications and AI-powered resume analysis",
    version="0.1.0",
)

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
    return {"status": "ok"}
