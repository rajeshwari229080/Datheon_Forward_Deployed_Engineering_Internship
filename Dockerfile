# ===================================================
# Stage 1: Build & Dependencies Stage
# ===================================================
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ===================================================
# Stage 2: Hardened Non-Root Production Runtime
# ===================================================
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/app/src"

# Security: Create non-privileged service user and group
RUN groupadd -g 10001 sentinel && \
    useradd -u 10001 -g sentinel -s /bin/bash -m sentinel && \
    mkdir -p /app/data /app/src && \
    chown -R sentinel:sentinel /app

COPY --from=builder /install /install
COPY --chown=sentinel:sentinel src /app/src
COPY --chown=sentinel:sentinel pyproject.toml /app/

# Switch to unprivileged non-root user
USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')" || exit 1

CMD ["python", "-m", "uvicorn", "sentinel.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
