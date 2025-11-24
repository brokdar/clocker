#!/bin/bash
set -e

echo "🚀 Initializing development environment..."
npm install -g @anthropic-ai/claude-code

echo "🔧 Installing dependencies..."
curl -LsSf https://astral.sh/uv/install.sh | sh

echo "📦 Setting up uv..."
uv sync

echo "🔧 Setting up pre-commit hooks..."
pip install pre-commit
pre-commit install
pre-commit autoupdate

echo "✅ Development environment setup complete!"
