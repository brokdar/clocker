#!/bin/bash
set -e

echo "🚀 Initializing development environment..."

# Configure Git safe directory
echo "🔒 Configuring Git safe directory..."
git config --global --add safe.directory /workspace

# Initialize backend
echo "📦 Setting up backend..."
uv sync

# Initialize pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install
pre-commit autoupdate

echo "✅ Development environment setup complete!"
