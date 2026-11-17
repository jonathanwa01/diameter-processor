FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY README.md ./
RUN uv sync --frozen --no-install-project --no-dev

COPY main.py ./
COPY src/ ./src/
COPY config/config.docker.yaml ./config/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

CMD ["python", "main.py", "--config", "config/config.docker.yaml"]
