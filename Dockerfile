FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ ./src

RUN pip install --upgrade pip
RUN pip install ".[ml,infra]"

COPY . /app

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "job_coach.app.main:app", "--host", "0.0.0.0", "--port", "8000"]