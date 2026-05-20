# CouchSurfing Backend

FastAPI-based backend for P2P accommodation exchange platform.

## Tech Stack

- **Python**: 3.10+
- **Framework**: FastAPI (async)
- **Database**: PostgreSQL + AsyncPG
- **ORM**: SQLAlchemy 2.0 (async mode)
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Auth**: JWT (python-jose), passlib[bcrypt]
- **Logging**: structlog
- **Server**: Uvicorn

## Project Structure

```
backend/
├── app/
│   ├── core/           # Configuration, database, logging, exceptions
│   ├── routers/        # API route handlers
│   ├── services/       # Business logic
│   ├── crud/          # Database operations
│   ├── schemas/       # Pydantic models
│   ├── models.py      # SQLAlchemy models
│   └── main.py        # Application entry point
├── alembic/           # Database migrations
├── requirements.txt   # Python dependencies
└── .env              # Environment variables
```

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- pip or poetry

### Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Run migrations:
```bash
alembic upgrade head
```

5. Start server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Development

### Running Tests

```bash
pytest
```

### Code Style

```bash
black app/
isort app/
flake8 app/
```

## Database Schema

### Core Entities

1. **User** - System users (guests, hosts, moderators)
2. **Listing** - Accommodation offerings
3. **Booking** - Reservation requests with state machine
4. **Review** - Ratings and comments
5. **Message** - User communication

### Booking State Machine

```
new -> pending -> confirmed -> completed
                    |-> rejected
                    |-> cancelled
```

## License

MIT
