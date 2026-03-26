FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Upgrade pip and add non-root user early
RUN useradd -m -s /bin/bash appuser

# Cache dependencies by using a dummy src structure
# This prevents re-installing dependencies if only source code changes
COPY pyproject.toml .
RUN mkdir -p src/job_coach && touch src/job_coach/__init__.py
RUN pip install ".[ml,infra]"

# Copy actual source code with correct ownership
# Using --chown here avoids an extra layer and doubles image size
COPY --chown=appuser:appuser . .

# Final installation of the project itself
RUN pip install --no-deps .

# Secure environment
USER appuser

EXPOSE 8000

CMD ["uvicorn", "job_coach.app.main:app", "--host", "0.0.0.0", "--port", "8000"]