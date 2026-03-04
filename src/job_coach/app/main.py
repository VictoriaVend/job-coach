from app.api.routes import jobs, users
from fastapi import FastAPI

app = FastAPI(title="Job Coach MVP")

# Роуты
app.include_router(users.router, prefix="/auth")
app.include_router(jobs.router, prefix="/jobs")


@app.get("/health")
def health_check():
    return {"status": "ok"}
