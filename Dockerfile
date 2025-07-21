# Build stage
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Runtime stage
FROM python:3.12-alpine
WORKDIR /app

# Copy only the necessary files from builder
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH"

CMD ["fastapi", "run", "app/main.py"]
