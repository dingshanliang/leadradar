from __future__ import annotations

from sqlmodel import SQLModel, Session, create_engine

from leadradar.config import get_settings


def get_engine():
    settings = get_settings()
    return create_engine(settings.database_url, echo=settings.app_env == "development")


def create_db_and_tables() -> None:
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_session():
    engine = get_engine()
    with Session(engine) as session:
        yield session
