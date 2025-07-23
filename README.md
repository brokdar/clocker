# Clocker

A modern time tracking FastAPI application for logging work hours, managing calendar entries, and monitoring compliance with German labor laws. Built with Python 3.12, FastAPI, and SQLModel.

## Features

### **Time Tracking**

- **Work & Travel Logs**: Track work hours and business travel with start/end times
- **Pause Management**: Record break times with automatic gap detection
- **Open-ended Logs**: Support for ongoing work sessions (work logs only)
- **Non-overlapping Validation**: Prevents time conflicts within the same day
- **Real-time Calculations**: Automatic duration calculations including breaks

### **Calendar Management**

- **Entry Types**: Work, Flextime, Vacation, Holiday, and Sick days
- **German Holiday Integration**: Automatic public holiday detection by state
- **Monthly/Yearly Views**: Comprehensive calendar navigation
- **Bulk Operations**: Create entries across date ranges with weekend filtering
- **Copy/Paste System**: Duplicate entries efficiently with keyboard shortcuts

### **Statistics & Compliance**

- **German Labor Law Compliance**: Monitor work hours, break requirements, and rest periods
- **Flextime Tracking**: Track overtime/undertime based on 8-hour standard days
- **Violation Detection**: Automatic flagging of compliance issues
- **Yearly Analytics**: Comprehensive statistics with day counts and work hours
- **Configurable Rules**: Customizable work hour limits and break requirements

### **Dual Interface**

- **REST API**: Full RESTful API with OpenAPI documentation
- **Web Interface**: Modern, responsive web UI with real-time interactions
- **Keyboard Shortcuts**: Power-user features (Ctrl+C/V, Delete)
- **Toast Notifications**: Non-intrusive success/error messaging

## Quick Start

### Using Docker (Recommended)

```bash
# Build the Docker image
docker build -t clocker .

# Run the application
docker run -d --name clocker -p 8000:8000 clocker

# Access the application
open http://localhost:8000
```

### Local Development

```bash
# Install dependencies
uv sync

# Set up pre-commit hooks
pre-commit install

# Run development server
uv run fastapi dev app/main.py

# Access the application
open http://localhost:8000
```

## Installation

### Prerequisites

- Python 3.12+
- UV package manager (recommended) or pip

### Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd clocker
   ```

2. **Install dependencies**

   ```bash
   # Using UV (recommended)
   uv sync

   # Or using pip
   pip install -e .
   ```

3. **Set up development tools**

   ```bash
   pre-commit install
   ```

4. **Run the application**

   ```bash
   # Development server with hot reload
   uv run fastapi dev app/main.py

   # Production server
   uv run fastapi run app/main.py
   ```

### Dev Container

This project includes a complete dev container setup for consistent development environments:

```bash
# Open in VS Code with dev containers extension
code .
# VS Code will prompt to reopen in container
```

### Web Interface Routes

- `/` - Redirect to current month calendar
- `/calendar/{year}/{month}/view` - Monthly calendar view
- `/entries/{date}/view` - Individual entry management
- `/statistics/{year}/view` - Yearly statistics overview

### Interactive API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Architecture

### Core Components

```text
app/
├── main.py              # FastAPI application setup
├── model.py             # Data models (CalendarEntry, TimeLog)
├── database.py          # Repository pattern with async SQLAlchemy
├── dependencies.py      # FastAPI dependency injection
├── routes/
│   ├── api/            # REST API endpoints
│   └── web/            # Web interface routes
├── services/
│   ├── calendar.py     # Calendar business logic
│   ├── time_logger.py  # Time log operations
│   ├── statistics.py   # Analytics and compliance
│   └── display.py      # Formatting utilities
├── static/             # CSS, JavaScript, assets
├── templates/          # Jinja2 HTML templates
└── utils/
    └── timely.py       # Time calculation utilities
```

### Data Models

#### CalendarEntry

Represents a single day with type and associated time logs:

- **Types**: Work, Flextime, Vacation, Holiday, Sick
- **Relationships**: One-to-many with TimeLog
- **Business Rules**: Only work entries can have time logs

#### TimeLog

Individual time tracking entries within a calendar day:

- **Types**: Work (can be open-ended), Travel (must be complete)
- **Validation**: No overlapping logs, pause limits, time range validation
- **Features**: Automatic duration calculations, pause tracking

### Database

- **SQLite** with async support (SQLAlchemy + aiosqlite)
- **SQLModel** for Pydantic integration and type safety
- **Repository Pattern** for clean data access
- **Automatic Schema Creation** on startup

## Development

### Code Quality

```bash
# Linting and formatting
uv run ruff check --fix
uv run ruff format

# Type checking
uv run mypy .

# Run all quality checks
pre-commit run --all-files
```

### Configuration

The application uses configuration files for statistics rules:

- **Statistics Config**: YAML-based configuration for work hour limits, break requirements, and compliance rules
- **Holiday Integration**: Supports different German states (default: Baden-Württemberg)

## Deployment

### Docker Production Build

```bash
# Build optimized production image
docker build -t clocker .

# Run with custom database path
docker run -d \
  --name clocker \
  -p 8000:8000 \
  -v /path/to/data:/app/data \
  clocker
```

### CI/CD

The project includes GitHub Actions for:

- **Multi-architecture builds** (linux/amd64, linux/arm64)
- **Container registry publishing** (GitHub Container Registry)
- **Automated builds** on main branch pushes

### Environment Variables

- `DATABASE_URL` - Custom database connection string
- Database files are stored in `/app/data/clocker.db` by default

## Business Rules & Compliance

### German Labor Law Compliance

- **Maximum Work Hours**: Configurable daily limits (default: 10 hours)
- **Break Requirements**:
  - 30 minutes for 6+ hour days
  - 45 minutes for 9+ hour days
- **Rest Period**: Minimum 11 hours between work days
- **Violation Tracking**: Automatic detection and reporting

### Time Tracking Rules

- Only work-type calendar entries can have time logs
- Time logs cannot overlap within the same day
- Only one open-ended work log allowed per day
- Travel logs must have both start and end times
- Pause durations cannot exceed total log duration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Technology Stack

- **Backend**: FastAPI, SQLModel, SQLAlchemy, aiosqlite
- **Frontend**: Jinja2 templates, vanilla JavaScript, CSS3
- **Database**: SQLite with async support
- **Development**: UV package manager, Ruff, MyPy, pytest
- **Deployment**: Docker, GitHub Actions, multi-architecture builds
- **Code Quality**: Pre-commit hooks, comprehensive linting, type checking
