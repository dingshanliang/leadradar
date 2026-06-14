"""Tests for follow-up schema extension (next_action_at + structured result)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from leadradar.main import app
from leadradar.models import (
    FollowUp,
    Lead,
    LeadScore,
    LeadStatus,
    Organization,
    RawDocument,
    Signal,
    Source,
)


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


def _seed_source(session, **kwargs) -> Source:
    defaults = {"name": "测试政府采购网", "source_type": "government_procurement"}
    defaults.update(kwargs)
    source = Source(**defaults)
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


def _seed_document(session, source: Source, **kwargs) -> RawDocument:
    defaults = {
        "source_id": source.id,
        "url": "https://example.gov.cn/notice/001",
        "title": "某县农产品品牌建设采购意向",
        "extracted_text": "采购单位：某县农业农村局\n预算金额：180万元",
        "parse_status": "completed",
    }
    defaults.update(kwargs)
    doc = RawDocument(**defaults)
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def _seed_org(session, **kwargs) -> Organization:
    defaults = {"name": "某县农业农村局", "normalized_name": "某县农业农村局"}
    defaults.update(kwargs)
    org = Organization(**defaults)
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


def _seed_signal(session, doc: RawDocument, org: Organization, **kwargs) -> Signal:
    defaults = {
        "raw_document_id": doc.id,
        "organization_id": org.id,
        "signal_type": "procurement_intent",
        "title": "某县农产品品牌建设采购意向",
        "budget_amount": 1800000,
        "confidence": 0.92,
        "source_url": doc.url,
        "evidence_text": "预算金额：180万元",
    }
    defaults.update(kwargs)
    signal = Signal(**defaults)
    session.add(signal)
    session.commit()
    session.refresh(signal)
    return signal


def _seed_lead(session, org: Organization, signal: Signal, **kwargs) -> Lead:
    defaults = {
        "organization_id": org.id,
        "primary_signal_id": signal.id,
        "customer_type": "region_brand_government",
        "recommended_package": "区域品牌数字化管理包",
        "budget_bucket": "100-500万",
        "lead_status": LeadStatus.NEW,
    }
    defaults.update(kwargs)
    lead = Lead(**defaults)
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


def _seed_score(session, lead: Lead, **kwargs) -> LeadScore:
    defaults = {
        "lead_id": lead.id,
        "total_score": 92,
        "grade": "S",
        "budget_strength_score": 35,
        "scenario_fit_score": 22,
        "timing_score": 20,
        "reachability_score": 10,
        "leverage_score": 5,
        "score_reason_json": json.dumps(["采购意向预算强信号"], ensure_ascii=False),
    }
    defaults.update(kwargs)
    score = LeadScore(**defaults)
    session.add(score)
    session.commit()
    session.refresh(score)
    return score


def _full_seed(session):
    source = _seed_source(session)
    doc = _seed_document(session, source)
    org = _seed_org(session)
    signal = _seed_signal(session, doc, org)
    lead = _seed_lead(session, org, signal)
    _seed_score(session, lead)
    return lead


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class TestCreateFollowUpWithNextActionAt:
    def test_create_follow_up_with_valid_next_action_at(self, client, session):
        lead = _full_seed(session)
        next_action_at = "2026-06-15T10:00:00+00:00"
        resp = client.post(
            f"/api/v1/leads/{lead.id}/follow-ups",
            json={
                "channel": "phone",
                "result_category": "未接通",
                "reason": "无人接听",
                "notes": "稍后再打",
                "next_action_at": next_action_at,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["next_action_at"] is not None
        assert _parse_datetime(data["next_action_at"]) == datetime(
            2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc
        )

        stored = session.exec(select(FollowUp)).first()
        assert stored is not None
        assert _parse_datetime(stored.next_action_at.isoformat()) == datetime(
            2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc
        )

    def test_create_follow_up_next_action_at_in_past(self, client, session):
        lead = _full_seed(session)
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        resp = client.post(
            f"/api/v1/leads/{lead.id}/follow-ups",
            json={
                "channel": "phone",
                "result_category": "未接通",
                "reason": "无人接听",
                "next_action_at": past,
            },
        )
        assert resp.status_code == 422
        assert resp.json()["detail"] == "下次跟进时间必须晚于当前时间"

    def test_create_follow_up_lead_not_found(self, client):
        resp = client.post(
            "/api/v1/leads/00000000-0000-0000-0000-000000000000/follow-ups",
            json={
                "channel": "phone",
                "result_category": "未接通",
                "reason": "无人接听",
            },
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Lead not found"

    def test_create_follow_up_without_next_action_at(self, client, session):
        lead = _full_seed(session)
        resp = client.post(
            f"/api/v1/leads/{lead.id}/follow-ups",
            json={
                "channel": "phone",
                "result_category": "未接通",
                "reason": "无人接听",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["next_action_at"] is None

    def test_create_follow_up_null_next_action_at(self, client, session):
        lead = _full_seed(session)
        resp = client.post(
            f"/api/v1/leads/{lead.id}/follow-ups",
            json={
                "channel": "phone",
                "result_category": "未接通",
                "reason": "无人接听",
                "next_action_at": None,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["next_action_at"] is None


class TestStructuredCallResult:
    def test_create_follow_up_with_category_and_reason(self, client, session):
        lead = _full_seed(session)
        resp = client.post(
            f"/api/v1/leads/{lead.id}/follow-ups",
            json={
                "channel": "phone",
                "result_category": "未接通",
                "reason": "无人接听",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["result_category"] == "未接通"
        assert data["reason"] == "无人接听"
        assert data["result"] == "未接通:无人接听"

        stored = session.exec(select(FollowUp)).first()
        assert stored.result == "未接通:无人接听"

    def test_reason_not_in_allowed_dictionary(self, client, session):
        lead = _full_seed(session)
        resp = client.post(
            f"/api/v1/leads/{lead.id}/follow-ups",
            json={
                "channel": "phone",
                "result_category": "未接通",
                "reason": "不存在的原因",
            },
        )
        assert resp.status_code == 422
        assert resp.json()["detail"] == "Invalid follow-up reason"

    def test_result_category_and_reason_mismatch(self, client, session):
        lead = _full_seed(session)
        resp = client.post(
            f"/api/v1/leads/{lead.id}/follow-ups",
            json={
                "channel": "phone",
                "result_category": "接通有意向",
                "reason": "无人接听",
            },
        )
        assert resp.status_code == 422
        assert resp.json()["detail"] == "结果类别与原因不匹配"

    def test_reason_missing(self, client, session):
        lead = _full_seed(session)
        resp = client.post(
            f"/api/v1/leads/{lead.id}/follow-ups",
            json={
                "channel": "phone",
                "result_category": "未接通",
            },
        )
        assert resp.status_code == 422
        assert resp.json()["detail"] == "reason 字段必填"

    def test_legacy_follow_up_without_category_is_readable(self, client, session):
        lead = _full_seed(session)
        follow_up = FollowUp(
            lead_id=lead.id,
            channel="phone",
            result="未接通",
            notes="legacy",
        )
        session.add(follow_up)
        session.commit()

        resp = client.get(f"/api/v1/leads/{lead.id}/follow-ups")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["result"] == "未接通"
        assert data[0]["result_category"] is None
        assert data[0]["reason"] is None


class TestSuggestDefaultNextActionAt:
    def test_suggestion_for_known_result(self, client):
        before = datetime.now(timezone.utc)
        resp = client.get("/api/v1/follow-up-suggestion", params={"result": "未接通"})
        after = datetime.now(timezone.utc)
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"] == "未接通"
        suggested = _parse_datetime(data["next_action_at"])
        assert suggested is not None
        expected_min = before + timedelta(hours=2)
        expected_max = after + timedelta(hours=2)
        assert expected_min <= suggested <= expected_max

    def test_suggestion_for_unknown_result(self, client):
        resp = client.get(
            "/api/v1/follow-up-suggestion", params={"result": "未知结果"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"] == "未知结果"
        assert data["next_action_at"] is None
