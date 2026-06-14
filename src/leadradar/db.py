from __future__ import annotations

from pathlib import Path

import yaml
from sqlmodel import SQLModel, Session, create_engine, select

from leadradar.config import get_settings


def get_engine():
    settings = get_settings()
    return create_engine(settings.database_url, echo=settings.app_env == "development")


def _data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data"


def seed_sources(session: Session) -> None:
    from leadradar.models import Source

    sources_path = _data_dir() / "sources.yml"
    if not sources_path.exists():
        return
    with open(sources_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    existing_keys = {s.source_key for s in session.exec(select(Source)).all() if s.source_key}
    for item in data.get("sources", []):
        key = item.get("id")
        if not key or key in existing_keys:
            continue
        source = Source(
            name=item["name"],
            source_type=item["source_type"],
            source_key=key,
            base_url=item.get("base_url"),
            priority=item.get("priority"),
            crawl_mode=item.get("crawl_mode"),
            enabled=item.get("enabled", True),
            rate_limit_per_minute=item.get("rate_limit_per_minute", 20),
        )
        session.add(source)
    session.commit()


def create_db_and_tables() -> None:
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_sources(session)


def get_session():
    engine = get_engine()
    with Session(engine) as session:
        yield session
