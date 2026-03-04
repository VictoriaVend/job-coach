from fastapi import FastAPI

from .routes import jobs, users

app = FastAPI()

app.include_router(users.router, prefix="/auth")
app.include_router(jobs.router, prefix="/jobs")
