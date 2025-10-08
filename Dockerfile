# Multi-stage for smaller image
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (if needed later)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8501

# Allow platforms to set PORT; default 8501
ENV PORT=8501

CMD ["streamlit", "run", "Subejct-PlaningV1.py", "--server.port", "${PORT}", "--server.address", "0.0.0.0"]

