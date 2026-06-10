from typing import Iterator
from sqlmodel import SQLModel, create_engine, Session
from .config import DB_PATH

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{DB_PATH}",
            connect_args={"check_same_thread": False},
        )
    return _engine


def _ensure_columns(engine) -> None:
    """Idempotently add columns introduced after a DB was first created.

    create_all() provisions missing tables but never ALTERs an existing one.
    Append ALTER TABLE statements here as the schema grows so an already-deployed
    fitai.db keeps working after an upgrade."""
    return


def init_db() -> None:
    import app.models  # noqa: F401  (register tables)
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    _ensure_columns(engine)


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
