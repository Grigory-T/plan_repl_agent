FROM python:3.13

WORKDIR /app

# --- System env ---
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# --- System deps (BUILD-TIME ROOT) ---
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     tesseract-ocr \
#     tesseract-ocr-rus \
#     poppler-utils \
#     && rm -rf /var/lib/apt/lists/*

# --- Create non-root user ---
RUN groupadd -g 1000 agent \
 && useradd -u 1000 -g agent -m agent

# --- Prepare app dirs and ownership ---
RUN mkdir -p /app/venv /app/work /app/logs /app/home /app/agent_spool \
 && chown -R agent:agent /app

# --- Switch to non-root BEFORE venv ---
USER agent
ENV HOME=/app/home

# --- Create venv as agent ---
RUN python -m venv $VIRTUAL_ENV \
 && pip install --upgrade pip

# --- Python deps (installed into venv as agent) ---
COPY requirements.txt .
RUN pip install -r requirements.txt

# --- Runtime env ---
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "agent.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
