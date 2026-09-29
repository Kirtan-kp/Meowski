FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/home/app/.cache/huggingface
ENV FLASHRANK_CACHE_DIR=/home/app/.cache/flashrank

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-runtime.txt .

RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.13.0

RUN pip install --no-cache-dir -r requirements-runtime.txt

RUN useradd --create-home --uid 10001 app \
    && mkdir -p /home/app/.cache/huggingface /home/app/.cache/flashrank \
    && chown -R app:app /home/app /app

COPY --chown=app:app app ./app
COPY --chown=app:app data ./data
COPY --chown=app:app scripts ./scripts

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]