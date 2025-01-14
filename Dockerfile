FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application files
COPY . .

# Install dependencies using uv
RUN uv venv
RUN uv sync --frozen

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uv", "run", "-m", "clocker"]
