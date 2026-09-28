"""PostgreSQL connectivity (SQLAlchemy + psycopg).

Phase 7: stores methodology state, knowledge items, provenance, and the
human-approval workflow. Connections are lazy so the API can boot even if the
database is temporarily unavailable.
"""

from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create all tables (idempotent). Imported here to avoid circular imports."""
    from app.models.orm import Base  # noqa: PLC0415

    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_connection() -> dict:
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar_one()
        return {"available": True, "version": version}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": str(exc)}
