# Multi-stage Django build
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static at build time (can be skipped if using volume)
RUN python manage.py collectstatic --noinput || echo "collectstatic skipped"

EXPOSE 8000
CMD ["gunicorn", "football_management_system.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
