FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
COPY src ./src

RUN pip install --upgrade pip
RUN pip install .

CMD ["python", "-m", "job_coach.main"]