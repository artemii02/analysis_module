FROM python:3.11-slim

ARG TORCH_PACKAGE=torch==2.7.1
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
ARG INSTALL_QLORA_DEPS=false

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    HF_HOME=/app/.hf-cache

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY main.py ./
COPY training/artifacts ./training/artifacts

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --index-url ${TORCH_INDEX_URL} ${TORCH_PACKAGE} \
    && pip install --no-cache-dir ".[hf_runtime]" \
    && if [ "$INSTALL_QLORA_DEPS" = "true" ]; then pip install --no-cache-dir ".[qlora]"; fi

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "interview_analysis.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
