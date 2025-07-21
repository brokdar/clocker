FROM mcr.microsoft.com/devcontainers/python:3.12

# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

RUN npm install -g @anthropic-ai/claude-code

# Install uv package manager and pre-commit
RUN pip install --no-cache-dir uv pre-commit

# Create directory and set permissions during build
RUN mkdir -p .devcontainer && \
    touch .devcontainer/startup.sh && \
    chmod +x .devcontainer/startup.sh

# Set workspace folder
WORKDIR /workspace
