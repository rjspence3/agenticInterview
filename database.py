"""
Database configuration and session management.

This module sets up SQLAlchemy and provides database connectivity.
Supports SQLite for development and PostgreSQL for production.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

# Database URL - defaults to SQLite for local development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./agentic_interview.db"
)

# Create engine
# SQLite-specific: check_same_thread=False allows multiple threads
# For PostgreSQL, this parameter is ignored
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False  # Set to True for SQL logging during development
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db() -> Session:
    """
    Get a database session.

    Usage:
        db = get_db()
        try:
            # Use db...
        finally:
            db.close()

    Returns:
        SQLAlchemy Session
    """
    return SessionLocal()


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.

    Usage:
        with get_db_session() as db:
            # Use db...
            # Automatically commits on success, rolls back on error

    Yields:
        SQLAlchemy Session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables.

    This should be called once at application startup.
    In production, use Alembic migrations instead.
    """
    from db_models import (
        Organization, Person, InterviewTemplate, TemplateQuestion,
        InterviewSession, TranscriptEntry, QuestionEvaluation
    )
    Base.metadata.create_all(bind=engine)


def drop_all_tables():
    """
    Drop all tables in the database.

    WARNING: This will delete all data!
    Only use for testing or development reset.
    """
    Base.metadata.drop_all(bind=engine)


# Test database support
def get_test_db_engine():
    """
    Create an in-memory SQLite engine for testing.

    Returns:
        SQLAlchemy Engine configured for in-memory SQLite
    """
    from sqlalchemy import create_engine
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )
    return engine


def init_test_db(engine):
    """
    Initialize test database with all tables.

    Args:
        engine: SQLAlchemy engine to use
    """
    from db_models import (
        Organization, Person, InterviewTemplate, TemplateQuestion,
        InterviewSession, TranscriptEntry, QuestionEvaluation
    )
    Base.metadata.create_all(bind=engine)
