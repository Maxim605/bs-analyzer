# ---- Build stage ----
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies for native packages (numpy, scipy, scikit-learn)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime stage ----
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY proto/ ./proto/
COPY src/ ./src/
COPY thrift/ ./thrift/
COPY scripts/ ./scripts/

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=8 \
    MKL_NUM_THREADS=8 \
    NUMEXPR_NUM_THREADS=8 \
    OPENBLAS_NUM_THREADS=8 \
    VECLIB_MAXIMUM_THREADS=8 \
    PORT=8000

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT}"]
