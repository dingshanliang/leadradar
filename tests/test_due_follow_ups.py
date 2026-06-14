"""Tests for due follow-ups endpoint and badge count (AC-01, AC-02 data)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from leadradar.auth import User, create_access_token
from leadradar.main import app
from leadradar.models import FollowUp, Lead, LeadStatus, Organization


@pytest.fixture
def engine():
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
def client(engine):
    from leadradar.db import get_session as _gs

    def _get_session_override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[_gs] = _get_session_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed_user(session: Session, email: str = "test@example.com") -> User:
    user = User(
        email=email,
        hashed_password="$2b$12$hashed-password-placeholder",
        role="sales",
        display_name="Test User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


def _seed_org(session: Session, name: str = "某县农业农村局") -> Organization:
    org = Organization(name=name, normalized_name=name)
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


def _seed_lead(
    session: Session,
    org: Organization,
    status: LeadStatus = LeadStatus.NEW,
) -> Lead:
    lead = Lead(
        organization_id=org.id,
        lead_status=status,
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


def _seed_follow_up(
    session: Session,
    lead: Lead,
    next_action_at: datetime,
    result: str = "未接通:无人接听",
) -> FollowUp:
    follow_up = FollowUp(
        lead_id=lead.id,
        channel="phone",
        result=result,
        next_action_at=next_action_at,
    )
    session.add(follow_up)
    session.commit()
    session.refresh(follow_up)
    return follow_up


class TestListDueFollowUps:
    """AC-01: Backend returns due follow-ups excluding terminal statuses."""

    def test_ac01_list_only_non_terminal_due_follow_ups(self, client, session):
        """List due follow-ups, exclude terminal-status leads, sorted ascending."""
        user = _seed_user(session)
        org_a = _seed_org(session, name="机构A")
        org_b = _seed_org(session, name="机构B")
        org_c = _seed_org(session, name="机构C（已成交）")

        lead_a = _seed_lead(session, org_a, LeadStatus.NEW)
        lead_b = _seed_lead(session, org_b, LeadStatus.QUALIFIED)
        lead_c = _seed_lead(session, org_c, LeadStatus.WON)

        now = datetime.now(timezone.utc)
        fu_a = _seed_follow_up(session, lead_a, now - timedelta(days=1))
        fu_b = _seed_follow_up(session, lead_b, now + timedelta(days=3))
        _seed_follow_up(session, lead_c, now - timedelta(hours=1))

        resp = client.get("/api/v1/follow-ups/due", headers=_auth_headers(user))

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["follow_up_id"] == str(fu_a.id)
        assert data[1]["follow_up_id"] == str(fu_b.id)
        assert data[0]["organization_name"] == "机构A"
        assert data[1]["organization_name"] == "机构B"
        assert data[0]["next_action_at"] <= data[1]["next_action_at"]

    def test_ac01_e1_unauthorized_request(self, client):
        """Missing JWT token returns 401."""
        resp = client.get("/api/v1/follow-ups/due")
        assert resp.status_code == 401

    def test_ac01_b1_empty_list(self, client, session):
        """No due follow-ups or all terminal leads returns 200 and empty list."""
        user = _seed_user(session)
        org = _seed_org(session)
        lead = _seed_lead(session, org, LeadStatus.LOST)
        now = datetime.now(timezone.utc)
        _seed_follow_up(session, lead, now - timedelta(hours=1))

        resp = client.get("/api/v1/follow-ups/due", headers=_auth_headers(user))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_ac01_b2_future_follow_ups_beyond_7_days_excluded(self, client, session):
        """A follow-up 10 days in the future is not included."""
        user = _seed_user(session)
        org = _seed_org(session)
        lead = _seed_lead(session, org, LeadStatus.NEW)
        now = datetime.now(timezone.utc)
        _seed_follow_up(session, lead, now + timedelta(days=10))

        resp = client.get("/api/v1/follow-ups/due", headers=_auth_headers(user))
        assert resp.status_code == 200
        assert resp.json() == []


class TestDueFollowUpCount:
    """Data backing the sidebar badge (AC-02)."""

    def test_ac02_count_returns_exact_due_count(self, client, session):
        """Badge count endpoint returns the exact number of due follow-ups."""
        user = _seed_user(session)
        now = datetime.now(timezone.utc)
        for i in range(3):
            org = _seed_org(session, name=f"机构{i}")
            lead = _seed_lead(session, org, LeadStatus.NEW)
            _seed_follow_up(session, lead, now + timedelta(hours=i + 1))

        resp = client.get("/api/v1/follow-ups/due/count", headers=_auth_headers(user))
        assert resp.status_code == 200
        assert resp.json() == {"count": 3}

    def test_ac02_e1_count_zero(self, client, session):
        """Badge count endpoint returns 0 when no due follow-ups exist."""
        user = _seed_user(session)
        resp = client.get("/api/v1/follow-ups/due/count", headers=_auth_headers(user))
        assert resp.status_code == 200
        assert resp.json() == {"count": 0}

    def test_ac02_b1_count_large_number(self, client, session):
        """Badge count endpoint returns the full count; UI caps at 99+."""
        user = _seed_user(session)
        now = datetime.now(timezone.utc)
        for i in range(150):
            org = _seed_org(session, name=f"机构{i}")
            lead = _seed_lead(session, org, LeadStatus.NEW)
            _seed_follow_up(session, lead, now + timedelta(hours=1))

        resp = client.get("/api/v1/follow-ups/due/count", headers=_auth_headers(user))
        assert resp.status_code == 200
        assert resp.json() == {"count": 150}

    def test_ac02_count_unauthorized(self, client):
        """Count endpoint also requires authentication."""
        resp = client.get("/api/v1/follow-ups/due/count")
        assert resp.status_code == 401
