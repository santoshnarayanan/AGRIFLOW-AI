# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — builder
#
# Installs all Python dependencies (including those that require build tools)
# into an isolated virtualenv.  Build tools and compiler artefacts are left
# behind and never reach the runtime image.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Keeps Python from buffering stdout/stderr (important for structured logging)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install build dependencies needed by psycopg2 / cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — runtime
#
# Minimal image: copies only the compiled virtualenv and application source.
# Runs as a non-root user — required for Azure Container Apps / AKS PSP.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    # Default to production-safe values; override via env_file or K8s secrets
    APP_ENV=production \
    LOG_FORMAT=json \
    LOG_LEVEL=INFO

# Runtime dependency for asyncpg / psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy virtualenv from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 8000

# CMD (not ENTRYPOINT) allows docker-compose / CI to override with
# `alembic upgrade head` without rebuilding the image.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
