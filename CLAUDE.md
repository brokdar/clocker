# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clocker is a time tracking FastAPI application that allows users to log work hours, manage calendar entries, and view statistics. The application runs in a devcontainer environment with full Docker support.

## Development Commands

### Environment Setup

- `uv sync` - Install dependencies using UV package manager
- `pre-commit install` - Set up git hooks for code quality checks

### Code Quality

- `uv run ruff check --fix` - Lint and auto-fix code with Ruff
- `uv run ruff format` - Format code with Ruff
- `uv run mypy .` - Type checking with MyPy

### Testing

- `uv run pytest` - Run all tests
- `uv run pytest tests/unit` - Run unit tests only

### Running the Application

- `uv run fastapi dev app/main.py` - Development server with hot reload
- `uv run fastapi run app/main.py` - Production server
- `docker build -t clocker .` - Build Docker image
- `docker run -p 8000:8000 clocker` - Run containerized application

## Architecture

### Core Data Models (`app/model.py`)

- `CalendarEntry`: Represents a day with type (work, vacation, holiday, etc.) and associated time logs
- `TimeLog`: Individual time tracking entries with start/end times, type (work/travel), and pause durations
- Validation logic ensures no overlapping time logs and proper time ranges

### Repository Pattern (`app/database.py`)

- `CalendarRepository`: Handles all database operations for calendar entries
- Uses SQLModel with async SQLAlchemy for database operations
- SQLite database with automatic table creation

### Service Layer

- `app/services/time_logger.py`: Business logic for time log operations (add, update, remove)
- `app/services/calendar.py`: Calendar-related operations
- `app/services/statistics.py`: Statistics and reporting functionality

### API Structure

- Dual API design: RESTful API routes (`app/routes/api/`) and web interface routes (`app/routes/web/`)
- FastAPI with Jinja2 templates for web UI
- Static files served from `app/static/`

### Time Utilities (`app/utils/timely.py`)

- Custom utilities for time calculations and formatting
- Handles time deltas and duration calculations

## Development Environment

This project runs in a devcontainer with:

- Python 3.12 with UV package manager
- Pre-commit hooks for code quality
- VS Code extensions for Python development, linting, and Docker support
- Automatic dependency installation via `.devcontainer/startup.sh`

## Key Business Rules

- Only work-type calendar entries can have time logs
- Time logs cannot overlap within the same day
- Only one open-ended (no end time) work log is allowed per day
- Travel logs must have both start and end times
- Pause durations cannot exceed the total time log duration
