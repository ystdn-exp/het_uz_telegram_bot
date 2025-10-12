```
telegram-bot-project/
├── alembic/                          # Database migrations
│   ├── versions/
│   └── env.py
│
├── src/
│   ├── bot/                          # Bot-specific code
│   │   ├── handlers/                 # Message handlers by domain
│   │   │   ├── __init__.py
│   │   │   ├── start.py             # /start command handler
│   │   │   ├── admin.py             # Admin handlers
│   │   │   ├── user.py              # User-related handlers
│   │   │   └── payments.py          # Payment handlers
│   │   │
│   │   ├── middlewares/             # Custom middlewares
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # Authentication middleware
│   │   │   ├── throttling.py        # Rate limiting
│   │   │   └── logging.py           # Logging middleware
│   │   │
│   │   ├── filters/                 # Custom filters
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   └── chat_type.py
│   │   │
│   │   ├── keyboards/               # Keyboard builders
│   │   │   ├── __init__.py
│   │   │   ├── inline.py
│   │   │   └── reply.py
│   │   │
│   │   ├── states/                  # FSM states
│   │   │   ├── __init__.py
│   │   │   └── registration.py
│   │   │
│   │   ├── utils/                   # Bot utilities
│   │   │   ├── __init__.py
│   │   │   ├── commands.py          # Command helpers
│   │   │   └── notifications.py
│   │   │
│   │   ├── loader.py                # Bot instance and dispatcher
│   │   └── constants.py             # Bot-specific constants
│   │
│   ├── api/                         # FastAPI application
│   │   ├── v1/                      # API versioning
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── users.py
│   │   │   │   ├── webhook.py       # Webhook endpoint
│   │   │   │   └── health.py
│   │   │   └── router.py
│   │   │
│   │   ├── dependencies.py          # FastAPI dependencies
│   │   ├── schemas.py               # API Pydantic models
│   │   └── middlewares.py
│   │
│   ├── services/                    # Business logic layer
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── payment_service.py
│   │   └── notification_service.py
│   │
│   ├── database/                    # Database layer
│   │   ├── models/                  # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   └── order.py
│   │   │
│   │   ├── repositories/            # Repository pattern
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── user_repository.py
│   │   │
│   │   └── connection.py            # DB connection management
│   │
│   ├── core/                        # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py                # Global settings (Pydantic BaseSettings)
│   │   ├── security.py              # Security utilities
│   │   ├── logging_config.py
│   │   └── exceptions.py            # Custom exceptions
│   │
│   ├── schemas/                     # Shared Pydantic schemas
│   │   ├── __init__.py
│   │   ├── base.py                  # Base schema with common configs
│   │   └── user.py
│   │
│   └── main.py                      # Application entry point
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_services.py
│   │   └── test_handlers.py
│   └── integration/
│       ├── test_api.py
│       └── test_bot.py
│
├── scripts/                         # Utility scripts
│   ├── start_polling.py
│   └── start_webhook.py
│
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
│
├── .env.example
├── .env
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml                   # Ruff configuration
└── README.md
```
