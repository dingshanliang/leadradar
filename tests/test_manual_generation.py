"""Tests for manual lead generation API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from leadradar.crawlers.base import FetchProvider, RawPage, SearchProvider, SearchResult
from leadradar.crawlers.registry import register
from leadradar.main import app
from leadradar.models import Source


class FakeSearch(SearchProvider):
    async def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        return []


class FakeFetch(FetchProvider):
    async def fetch(self, url: str) -> RawPage:
        return RawPage(url=url, status_code=200, content_type="text/html", text="<html></html>")


def _fake_search_factory() -> FakeSearch:
    return FakeSearch()


def _fake_fetch_factory() -> FakeFetch:
    return FakeFetch()


def _register_test_source():
    register("test_source", _fake_search_factory, _fake_fetch_factory)


@pytest.fixture
def engine():
    _register_test_source()
    e = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(e)
    return e


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def sample_source(session):
    source = Source(
        name="测试采购网",
        source_type="government_procurement",
        source_key="test_source",
        enabled=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@pytest.fixture
def client(engine, monkeypatch):
    from leadradar.db import get_session
    from leadradar import api

    def _get_session():
        with Session(engine) as s:
            yield s

    # Prevent background tasks from running real crawls in API tests.
    async def _noop(*, task_id, background_tasks):
        return None

    monkeypatch.setattr(
        api.manual_generation_routes,
        "schedule_manual_task",
        _noop,
    )

    app.dependency_overrides[get_session] = _get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_manual_task(client, sample_source):
    response = client.post(
        "/api/v1/manual-tasks",
        json={
            "source_keys": ["test_source"],
            "keyword_mode": "by_group",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["total_subtasks"] > 0


def test_create_manual_task_requires_source_keys(client):
    response = client.post(
        "/api/v1/manual-tasks",
        json={"source_keys": [], "keyword_mode": "by_group"},
    )
    assert response.status_code == 422


def test_create_manual_task_rejects_unknown_source_key(client):
    response = client.post(
        "/api/v1/manual-tasks",
        json={"source_keys": ["not_real"], "keyword_mode": "by_group"},
    )
    assert response.status_code == 422


def test_list_manual_tasks(client, sample_source):
    client.post(
        "/api/v1/manual-tasks",
        json={
            "source_keys": ["test_source"],
            "keyword_mode": "by_group",
        },
    )
    response = client.get("/api/v1/manual-tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_manual_task_detail(client, sample_source):
    create_resp = client.post(
        "/api/v1/manual-tasks",
        json={
            "source_keys": ["test_source"],
            "keyword_mode": "by_group",
        },
    )
    task_id = create_resp.json()["id"]
    response = client.get(f"/api/v1/manual-tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert len(data["subtasks"]) > 0
