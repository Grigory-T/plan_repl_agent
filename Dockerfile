FROM python:3.12-slim

WORKDIR /app

# Install system packages (as root, before user switch)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-rus \
    poppler-utils \
    file \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install base packages globally
COPY requirements.txt .
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLCONFIGDIR=/app/lib/.matplotlib

EXPOSE 8000

# Note: docker-compose.yml sets user: "${UID:-1000}:${GID:-1000}"
CMD ["uvicorn", "agent.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]