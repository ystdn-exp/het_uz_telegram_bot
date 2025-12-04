# HET - Telegram Bot Platform

A production-ready, scalable Telegram bot platform built with FastAPI and Aiogram 3, featuring webhook-based message handling, multi-language support, and comprehensive background task scheduling.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)
- [Development Workflow](#development-workflow)
- [Database Migrations](#database-migrations)
- [Management Commands](#management-commands)
- [Internationalization](#internationalization)
- [Deployment](#deployment)
- [Project Status](#project-status)
- [Contributing](#contributing)

## Overview

HET is a modern Telegram bot platform designed with scalability and maintainability in mind. It uses a webhook-based approach for receiving Telegram updates through FastAPI, providing a solid foundation for building complex bot applications with proper separation of concerns, internationalization, and background task processing.

## Features

### Implemented

- **Webhook-based Architecture**: FastAPI web server for receiving Telegram updates
- **Multi-language Support**: i18n with Babel (English, Russian, Uzbek)
- **Background Job Scheduling**: APScheduler with Redis backend for persistent job storage
- **Error Monitoring**: Sentry integration for error tracking and performance monitoring
- **Advanced Logging**: Rotating file logging with configurable retention (10MB files, 5 backups)
- **Security**: IP whitelist middleware for validating Telegram webhook requests
- **Database Management**: Alembic migrations with async SQLAlchemy support
- **Management Commands**: Django-style CLI for administrative tasks
- **Docker Support**: Complete containerization with development and production configurations
- **CI/CD Pipeline**: GitHub Actions workflow for automated deployment

### In Development

- Bot conversation handlers and FSM states
- Database models and repository layer
- Service layer business logic
- Web scraping with Playwright
- Notification system
- Authentication and rate limiting middleware
- Comprehensive test suite

## Technology Stack

### Core

- **Python 3.13**: Latest Python version with async support
- **FastAPI 0.115.0**: Modern, fast web framework for building APIs
- **Aiogram 3.22.0**: Async framework for Telegram Bot API
- **SQLAlchemy 2.0.41**: Async ORM with PostgreSQL support
- **PostgreSQL**: Primary database
- **Redis 5.0.7**: Caching and job storage

### Background Processing

- **APScheduler 3.10.4**: Advanced Python Scheduler with Redis backend
- **Playwright 1.48.0**: Browser automation for web scraping

### Monitoring & Logging

- **Sentry SDK 2.15.0**: Error tracking and performance monitoring
- Custom rotating file logging system

### Development Tools

- **Alembic 1.16.1**: Database migration management
- **Typer 0.12.5**: CLI framework for management commands
- **Black 23.1.0**: Code formatting
- **isort 5.12.0**: Import sorting
- **flake8 6.0.0**: Linting
- **pre-commit 3.6.0**: Git hooks for code quality

### Infrastructure

- **Docker & Docker Compose**: Containerization
- **Gunicorn**: WSGI HTTP server
- **Uvicorn**: ASGI server with multiple workers
- **Ngrok**: Local webhook tunneling for development

## Architecture

The project follows a layered architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│           FastAPI Web Application Layer             │
│  (Webhook endpoint, Health checks, Middleware)      │
└───────────────────┬─────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────┐
│              Telegram Bot Layer                      │
│  (Handlers, Middlewares, Keyboards, States, FSM)    │
└───────────────────┬─────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────┐
│            Business Logic Layer                      │
│         (Services, Tasks, Commands)                  │
└───────────────────┬─────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────┐
│              Data Access Layer                       │
│      (Repositories, Models, Connections)             │
└───────────────────┬─────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────┐
│         PostgreSQL Database + Redis Cache            │
└─────────────────────────────────────────────────────┘
```

### Design Patterns

- **Repository Pattern**: Data access abstraction
- **Dependency Injection**: FastAPI dependencies for loose coupling
- **Middleware Pattern**: Request/response processing pipeline
- **Command Pattern**: Management commands for administrative tasks
- **FSM (Finite State Machine)**: Bot conversation state management

## Project Structure

```
.
├── alembic/                    # Database migrations
│   ├── versions/               # Migration versions
│   └── env.py                  # Alembic configuration
│
├── src/                        # Source code
│   ├── main.py                 # Application entry point
│   │
│   ├── core/                   # Core configuration
│   │   ├── config.py           # Settings (Pydantic BaseSettings)
│   │   ├── logging_config.py   # Logging setup
│   │   ├── scheduler.py        # APScheduler configuration
│   │   └── security.py         # Security utilities
│   │
│   ├── bot/                    # Telegram bot components
│   │   ├── handlers/           # Message handlers
│   │   │   ├── start.py        # /start command
│   │   │   ├── register.py     # Registration flow
│   │   │   └── users.py        # User-related handlers
│   │   │
│   │   ├── middlewares/        # Custom middlewares
│   │   │   ├── translations.py # i18n middleware
│   │   │   ├── auth.py         # Authentication
│   │   │   ├── throttling.py   # Rate limiting
│   │   │   └── logging.py      # Request logging
│   │   │
│   │   ├── keyboards/          # Keyboard builders
│   │   │   ├── inline.py       # Inline keyboards
│   │   │   └── reply.py        # Reply keyboards
│   │   │
│   │   ├── states/             # FSM states
│   │   │   └── registration.py # Registration states
│   │   │
│   │   ├── filters/            # Custom filters
│   │   ├── tasks/              # Bot-specific tasks
│   │   │   ├── scraper.py      # Web scraping
│   │   │   └── notifications.py# Notifications
│   │   │
│   │   ├── utils/              # Bot utilities
│   │   │   └── context_variables.py # i18n context
│   │   │
│   │   └── loader.py           # Bot and dispatcher setup
│   │
│   ├── web/                    # FastAPI web layer
│   │   ├── v1/                 # API versioning
│   │   │   └── endpoints/      # API endpoints
│   │   │       ├── webhook.py  # Telegram webhook
│   │   │       └── health.py   # Health check
│   │   │
│   │   ├── middlewares/        # Web middlewares
│   │   │   └── whitelist.py    # IP whitelist
│   │   │
│   │   ├── dependencies.py     # FastAPI dependencies
│   │   └── schemas.py          # Pydantic models
│   │
│   ├── database/               # Database layer
│   │   ├── models/             # SQLAlchemy models
│   │   │   ├── base.py         # Base model
│   │   │   └── users.py        # User model
│   │   │
│   │   ├── repositories/       # Repository pattern
│   │   │   ├── base.py         # Base repository
│   │   │   └── users.py        # User repository
│   │   │
│   │   └── connection.py       # DB connection management
│   │
│   ├── services/               # Business logic layer
│   │   ├── base.py             # Base service
│   │   └── scraper/            # Scraping services
│   │
│   ├── tasks/                  # Scheduled jobs
│   │   └── jobs.py             # APScheduler jobs
│   │
│   ├── commands/               # Management commands
│   │   ├── set_webhook.py      # Set Telegram webhook
│   │   └── remove_webhook.py   # Remove webhook
│   │
│   └── command_manager.py      # Command management system
│
├── locales/                    # i18n translations
│   ├── messages.pot            # Translation template
│   ├── en/LC_MESSAGES/         # English translations
│   ├── ru/LC_MESSAGES/         # Russian translations
│   └── uz/LC_MESSAGES/         # Uzbek translations
│
├── tests/                      # Test suite
│
├── requirements/               # Python dependencies
│   ├── base.txt                # Core dependencies
│   ├── development.txt         # Development tools
│   └── production.txt          # Production dependencies
│
├── .github/                    # GitHub workflows
│   └── workflows/
│       └── deploy.yaml         # Deployment pipeline
│
├── docker-compose.dev.yaml     # Development stack
├── docker-compose.prod.yaml    # Production stack
├── Dockerfile.development      # Development container
├── Dockerfile.production       # Production container
├── entrypoint.sh               # Container entrypoint
├── Makefile                    # Docker commands
├── manage.py                   # Management CLI
├── alembic.ini                 # Alembic configuration
├── babel.cfg                   # Babel configuration
├── pyproject.toml              # Black/isort config
├── setup.cfg                   # Flake8 config
├── .pre-commit-config.yaml     # Pre-commit hooks
├── .env.example                # Environment template
└── README.md                   # This file
```

## Prerequisites

- **Docker** and **Docker Compose** (recommended)
- **Python 3.13+** (for local development)
- **PostgreSQL 14+** (if running without Docker)
- **Redis** (if running without Docker)
- **Telegram Bot Token** (from [@BotFather](https://t.me/botfather))

## Installation

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd level_1
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Configure environment variables** (see [Configuration](#configuration))

4. **Install Playwright browsers** (for web scraping)
   ```bash
   docker-compose -f docker-compose.dev.yaml run --rm web playwright install
   ```

5. **Start the development stack**
   ```bash
   make dev-up
   ```

### Local Development (Without Docker)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd level_1
   ```

2. **Create virtual environment**
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements/development.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install
   ```

5. **Create environment file**
   ```bash
   cp .env.example .env
   ```

6. **Configure environment variables** (see [Configuration](#configuration))

7. **Start PostgreSQL and Redis**
   ```bash
   # Using Homebrew (macOS)
   brew services start postgresql@14
   brew services start redis

   # Or using your preferred method
   ```

8. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

## Configuration

### Environment Variables

Edit the `.env` file with your configuration:

```bash
# Environment mode (development, production)
ENVIRONMENT=development

# Secret key for application
SECRET_KEY=your-secret-key-here

# Database configuration
SQL_HOST=localhost              # Use host.docker.internal for Docker
SQL_PORT=5445                   # PostgreSQL port
SQL_USER=postgres               # Database user
SQL_PASSWORD=postgres           # Database password
SQL_DB=het                      # Database name

# Telegram Bot API
TELEGRAM_SECRET_KEY=your-telegram-secret-key
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Monitoring (optional)
SENTRY_DSN=your-sentry-dsn-url

# Development only - Ngrok for webhook tunneling
NGROK_AUTHTOKEN=your-ngrok-auth-token
```

### Getting Required Credentials

1. **Telegram Bot Token**:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Send `/newbot` and follow the instructions
   - Copy the bot token provided

2. **Telegram Secret Key**:
   - Generate a random secret key:
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```

3. **Ngrok Auth Token** (for local development):
   - Sign up at [ngrok.com](https://ngrok.com)
   - Get your auth token from the dashboard

4. **Sentry DSN** (optional):
   - Create account at [sentry.io](https://sentry.io)
   - Create a new Python project
   - Copy the DSN from project settings

## Running the Project

### Development Mode

**Using Docker:**
```bash
# Start all services (web, postgres, redis, ngrok)
make dev-up

# View logs
docker-compose -f docker-compose.dev.yaml logs -f web

# Stop all services
make dev-down
```

**Without Docker:**
```bash
# Start the application
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Setting Up the Webhook

After starting the application:

```bash
# Using management command
python manage.py set_webhook

# Or manually set webhook URL
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/api/v1/webhook"}'
```

### Accessing Services

- **Application**: http://localhost:8000
- **Health Check**: http://localhost:8000/healthz
- **PostgreSQL**: localhost:5445
- **Redis**: localhost:6379
- **Ngrok Dashboard**: http://localhost:4040 (development only)

### Production Mode

```bash
# Start production stack
make prod-up

# View logs
docker-compose -f docker-compose.prod.yaml logs -f web

# Stop production stack
make prod-down
```

## Development Workflow

### Code Quality

The project uses pre-commit hooks for code quality:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Format code
black src/
isort src/

# Lint code
flake8 src/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_services.py
```

### Project Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test locally**

3. **Run code quality checks**
   ```bash
   pre-commit run --all-files
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

5. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Database Migrations

### Creating Migrations

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration
alembic revision -m "description"
```

### Applying Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision>

# Downgrade one version
alembic downgrade -1

# View current version
alembic current

# View migration history
alembic history
```

### Migration Notes

- Migrations are automatically applied during container startup via `entrypoint.sh`
- Review auto-generated migrations before applying
- Test migrations on development database first

## Management Commands

The project includes a Django-style management command system:

```bash
# List all available commands
python manage.py --list

# Set Telegram webhook
python manage.py set_webhook

# Remove Telegram webhook
python manage.py remove_webhook
```

### Creating Custom Commands

1. Create a file in `src/commands/your_command.py`:
   ```python
   from src.command_manager import BaseCommand

   class Command(BaseCommand):
       help = "Description of your command"

       async def handle(self, *args, **kwargs):
           # Your command logic here
           self.log("Executing command...")
   ```

2. Run the command:
   ```bash
   python manage.py your_command
   ```

## Internationalization

### Supported Languages

- English (en)
- Russian (ru)
- Uzbek (uz)

### Adding Translations

1. **Mark strings for translation** in code:
   ```python
   from src.bot.utils.context_variables import _

   # In your handler
   message = _("Hello, world!")
   ```

2. **Extract messages**:
   ```bash
   pybabel extract -F babel.cfg -o locales/messages.pot .
   ```

3. **Update translation files**:
   ```bash
   pybabel update -i locales/messages.pot -d locales
   ```

4. **Edit translation files** in `locales/{lang}/LC_MESSAGES/messages.po`

5. **Compile translations**:
   ```bash
   pybabel compile -d locales
   ```

### User Language Detection

The application automatically detects user language through:
- User's Telegram language settings
- User's saved language preference in database
- Fallback to default language (English)

## Deployment

### Docker Hub Deployment

The project includes a GitHub Actions workflow for automated deployment:

1. **Configure secrets** in GitHub repository:
   - `DOCKER_USERNAME`: Docker Hub username
   - `DOCKER_PASSWORD`: Docker Hub password/token
   - `SSH_PRIVATE_KEY`: SSH key for production server
   - `SSH_HOST`: Production server hostname/IP
   - `SSH_USER`: SSH username

2. **Trigger deployment**:
   - Go to Actions tab in GitHub
   - Select "Deploy to Production"
   - Click "Run workflow"
   - Select branch and click "Run workflow"

### Manual Deployment

1. **Build Docker image**:
   ```bash
   docker build -f Dockerfile.production -t your-image-name:tag .
   ```

2. **Push to registry**:
   ```bash
   docker push your-image-name:tag
   ```

3. **Deploy on server**:
   ```bash
   ssh user@server
   cd /path/to/project
   docker-compose -f docker-compose.prod.yaml pull
   docker-compose -f docker-compose.prod.yaml up -d
   ```

### Environment Setup on Server

1. Create `.env` file with production credentials
2. Ensure PostgreSQL and Redis are running
3. Configure reverse proxy (Nginx) for HTTPS
4. Set up SSL certificates (Let's Encrypt)
5. Configure firewall rules

## Project Status

### Current Phase: Foundation & Architecture Setup

The project is currently in active development with a solid foundation in place.

#### Completed

- Complete infrastructure setup (Docker, PostgreSQL, Redis)
- Core configuration system with environment management
- Logging and error monitoring (Sentry)
- Multi-language support framework (en, ru, uz)
- Background job scheduling with APScheduler
- Security middleware (IP whitelist)
- Database migration system
- Management command framework
- CI/CD pipeline configuration
- Development and production environments

#### In Progress

- Bot conversation handlers
- Database models and repositories
- Service layer implementation
- Web scraping tasks
- Notification system
- FSM state implementations
- Keyboard builders
- Authentication and throttling middleware

#### Planned

- Comprehensive test suite
- API documentation (OpenAPI/Swagger)
- Admin panel
- Analytics and metrics
- Payment integration
- User management features
- Additional language support

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and code quality checks
5. Submit a pull request

### Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting (90 char line length)
- Use isort for import sorting
- Maximum complexity: 10 (flake8)
- Write descriptive commit messages
- Add docstrings to public functions/classes

### Commit Message Format

```
<type>: <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat: add user registration handler

Implements the user registration flow with FSM states
and validation logic.
```

## License

[Specify your license here]

## Contact

[Specify contact information or links]

---

**Note**: This project is under active development. Features and documentation may change. Check the repository regularly for updates.
