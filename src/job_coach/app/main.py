from fastapi import FastAPI

from job_coach.app.api.routes import analysis, jobs, rag, resume, users

app = FastAPI(title="AI-powered Job Coach")

# Роуты
app.include_router(users.router, prefix="/auth")
app.include_router(jobs.router, prefix="/jobs")
app.include_router(resume.router, prefix="/resume")
app.include_router(rag.router, prefix="/rag")
app.include_router(analysis.router, prefix="/analysis")


@app.get("/health")
def health_check():
    return {"status": "ok"}
