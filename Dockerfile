# Базовый образ
FROM python:3.14-slim

# Рабочая директория
WORKDIR /app

# Копируем pyproject.toml и src для кеширования слоев
COPY pyproject.toml .
COPY src/ ./src

# Обновляем pip и устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install ".[dev]"

# Копируем остальной проект (alembic, docker-compose и др.)
COPY . /app

# PYTHONPATH для корректного импорта
ENV PYTHONPATH=/app/src/job_coach

# Команда запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]