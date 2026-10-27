import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


# Schema this service writes to. Overridable so the same template works
# for other services (e.g. meeting-chat sets DB_SEARCH_PATH=vectordb, public).
_SEARCH_PATH = os.getenv("DB_SEARCH_PATH", "meetings, public")


class Base(DeclarativeBase):
    pass


# create_engine is lazy: no connection is opened until a session is used.
engine = create_engine(settings.database_url, pool_pre_ping=True)


@event.listens_for(engine, "connect")
def _set_search_path(dbapi_conn, _record):
    """Apply search_path on every pooled connection.

    Supavisor (Supabase's pooler) strips the `options=-csearch_path=...`
    parameter from the connection URL, so the URL alone cannot set the
    schema — verified empirically: current_schema() stayed 'public'
    with connect_args, but returned 'meetings' after an explicit SET.

    This listener runs once per physical connection, before any query,
    so every checkout from the pool inherits the correct search_path.
    """
    with dbapi_conn.cursor() as cur:
        cur.execute(f"SET search_path TO {_SEARCH_PATH}")
    # The DBAPI connection is not in autocommit mode here, so the SET
    # would be rolled back without an explicit commit.
    dbapi_conn.commit()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables. Imports models so Meeting is registered on Base.metadata."""
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
