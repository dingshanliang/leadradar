"""Tests for T-601/T-602/T-603: FastAPI CRUD, follow-up, and export endpoints."""

import csv
import io
import json
from uuid import uuid4

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select
from fastapi.testclient import TestClient

from leadradar.models import (
    Lead,
    LeadScore,
    LeadStatus,
    Organization,
    RawDocument,
    Signal,
    Source,
)
from leadradar.main import app


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
    """Seed a complete lead with all related entities."""
    source = _seed_source(session)
    doc = _seed_document(session, source)
    org = _seed_org(session)
    signal = _seed_signal(session, doc, org)
    lead = _seed_lead(session, org, signal)
    score = _seed_score(session, lead)
    return source, doc, org, signal, lead, score


# ════════════════════════════════════════════════════════════════
# T-601: Basic CRUD endpoints
# ════════════════════════════════════════════════════════════════


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestSourcesEndpoint:
    def test_list_sources_empty(self, client):
        resp = client.get("/api/v1/sources")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_sources_returns_seeded(self, client, session):
        _seed_source(session)
        resp = client.get("/api/v1/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "测试政府采购网"

    def test_source_has_expected_fields(self, client, session):
        _seed_source(session)
        resp = client.get("/api/v1/sources")
        source = resp.json()[0]
        assert "id" in source
        assert "name" in source
        assert "source_type" in source
        assert "enabled" in source


class TestLeadsEndpoint:
    def test_list_leads_empty(self, client):
        resp = client.get("/api/v1/leads")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_leads_with_data(self, client, session):
        _full_seed(session)
        resp = client.get("/api/v1/leads")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["grade"] == "S"
        assert data[0]["total_score"] == 92

    def test_list_leads_filter_by_grade(self, client, session):
        _full_seed(session)
        resp = client.get("/api/v1/leads", params={"grade": "A"})
        assert resp.status_code == 200
        assert resp.json() == []

        resp = client.get("/api/v1/leads", params={"grade": "S"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_leads_filter_by_status(self, client, session):
        _full_seed(session)
        resp = client.get("/api/v1/leads", params={"status": "qualified"})
        assert resp.json() == []

        resp = client.get("/api/v1/leads", params={"status": "new"})
        assert len(resp.json()) == 1

    def test_list_leads_pagination(self, client, session):
        source = _seed_source(session)
        doc = _seed_document(session, source)
        org = _seed_org(session)
        signal = _seed_signal(session, doc, org)
        for i in range(5):
            _seed_lead(session, org, signal, customer_type=f"type_{i}")

        # Seed scores for all leads so JOIN works
        leads = session.exec(select(Lead)).all()
        for lead in leads:
            _seed_score(session, lead)

        resp = client.get("/api/v1/leads", params={"limit": 2, "offset": 0})
        assert len(resp.json()) == 2

        resp = client.get("/api/v1/leads", params={"limit": 2, "offset": 4})
        assert len(resp.json()) == 1


class TestDocumentsEndpoint:
    def test_list_documents_empty(self, client):
        resp = client.get("/api/v1/documents")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_documents_returns_seeded(self, client, session):
        source = _seed_source(session)
        _seed_document(session, source)
        resp = client.get("/api/v1/documents")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "某县农产品品牌建设采购意向"

    def test_document_has_expected_fields(self, client, session):
        source = _seed_source(session)
        _seed_document(session, source)
        resp = client.get("/api/v1/documents")
        doc = resp.json()[0]
        assert "id" in doc
        assert "url" in doc
        assert "title" in doc
        assert "parse_status" in doc


# ════════════════════════════════════════════════════════════════
# T-602: Lead detail, follow-up, status update
# ════════════════════════════════════════════════════════════════


class TestLeadDetail:
    def test_lead_detail_not_found(self, client):
        fake_id = str(uuid4())
        resp = client.get(f"/api/v1/leads/{fake_id}")
        assert resp.status_code == 404

    def test_lead_detail_includes_score(self, client, session):
        _, _, _, _, lead, score = _full_seed(session)
        resp = client.get(f"/api/v1/leads/{lead.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(lead.id)
        assert data["score"]["total_score"] == 92
        assert data["score"]["grade"] == "S"

    def test_lead_detail_includes_call_script(self, client, session):
        _, _, _, _, lead, _ = _full_seed(session)
        resp = client.get(f"/api/v1/leads/{lead.id}")
        data = resp.json()
        script = data["call_script"]
        assert "opening" in script
        assert "questions" in script
        assert "wechat_follow_up" in script
        assert "农业农村局" in script["opening"]

    def test_lead_detail_includes_organization(self, client, session):
        _, _, org, _, lead, _ = _full_seed(session)
        resp = client.get(f"/api/v1/leads/{lead.id}")
        data = resp.json()
        assert data["organization"]["name"] == org.name

    def test_lead_detail_includes_signal(self, client, session):
        _, _, _, signal, lead, _ = _full_seed(session)
        resp = client.get(f"/api/v1/leads/{lead.id}")
        data = resp.json()
        assert data["signal"]["signal_type"] == "procurement_intent"
        assert data["signal"]["budget_amount"] == 1800000


class TestLeadStatusUpdate:
    def test_update_lead_status(self, client, session):
        _, _, _, _, lead, _ = _full_seed(session)
        resp = client.patch(
            f"/api/v1/leads/{lead.id}/status",
            json={"status": "qualified"},
        )
        assert resp.status_code == 200
        assert resp.json()["lead_status"] == "qualified"

    def test_update_lead_status_not_found(self, client):
        resp = client.patch(
            f"/api/v1/leads/{str(uuid4())}/status",
            json={"status": "qualified"},
        )
        assert resp.status_code == 404

    def test_update_lead_status_invalid(self, client, session):
        _, _, _, _, lead, _ = _full_seed(session)
        resp = client.patch(
            f"/api/v1/leads/{lead.id}/status",
            json={"status": "invalid_status"},
        )
        assert resp.status_code == 422


class TestFollowUp:
    def test_create_follow_up(self, client, session):
        _, _, _, _, lead, _ = _full_seed(session)
        resp = client.post(
            f"/api/v1/leads/{lead.id}/follow-ups",
            json={
                "channel": "phone",
                "result": "已联系，需跟进",
                "notes": "对方表示下周可约",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["channel"] == "phone"
        assert data["result"] == "已联系，需跟进"

    def test_list_follow_ups(self, client, session):
        _, _, _, _, lead, _ = _full_seed(session)
        client.post(
            f"/api/v1/leads/{lead.id}/follow-ups",
            json={"channel": "phone", "result": "第一次联系"},
        )
        client.post(
            f"/api/v1/leads/{lead.id}/follow-ups",
            json={"channel": "wechat", "result": "微信沟通"},
        )
        resp = client.get(f"/api/v1/leads/{lead.id}/follow-ups")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_follow_up_not_found_lead(self, client):
        resp = client.post(
            f"/api/v1/leads/{str(uuid4())}/follow-ups",
            json={"channel": "phone", "result": "测试"},
        )
        assert resp.status_code == 404


# ════════════════════════════════════════════════════════════════
# T-603: Export
# ════════════════════════════════════════════════════════════════


class TestExport:
    def test_export_csv(self, client, session):
        _full_seed(session)
        resp = client.get("/api/v1/leads/export", params={"format": "csv"})
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]

        reader = csv.DictReader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["grade"] == "S"
        assert rows[0]["organization_name"] == "某县农业农村局"

    def test_export_xlsx(self, client, session):
        _full_seed(session)
        resp = client.get("/api/v1/leads/export", params={"format": "xlsx"})
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]
        assert len(resp.content) > 0

    def test_export_csv_filter_by_grade(self, client, session):
        _full_seed(session)
        resp = client.get("/api/v1/leads/export", params={"format": "csv", "grade": "A"})
        reader = csv.DictReader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 0

    def test_export_invalid_format(self, client, session):
        resp = client.get("/api/v1/leads/export", params={"format": "pdf"})
        assert resp.status_code == 422
