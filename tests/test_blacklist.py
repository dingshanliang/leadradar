"""Tests for blacklist acceptance criteria."""

from __future__ import annotations

import json

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select
from fastapi.testclient import TestClient

from leadradar.auth import User, create_access_token
from leadradar.main import app
from leadradar.models import (
    Blocklist,
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


@pytest.fixture
def auth_token(session):
    user = User(email="test@example.com", hashed_password="x")
    session.add(user)
    session.commit()
    session.refresh(user)
    return create_access_token(user.id, user.role)


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


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


def _full_seed(session, lead_status: LeadStatus = LeadStatus.NEW):
    source = _seed_source(session)
    doc = _seed_document(session, source)
    org = _seed_org(session)
    signal = _seed_signal(session, doc, org)
    lead = _seed_lead(session, org, signal, lead_status=lead_status)
    score = _seed_score(session, lead)
    return source, doc, org, signal, lead, score


# ════════════════════════════════════════════════════════════════
# AC-01: Auto-Block Lead on Invalid/Refuse Follow-up
# ════════════════════════════════════════════════════════════════


class TestAutoBlockOnInvalidFollowUp:
    def test_ac01_submitting_invalid_follow_up_blocks_lead(self, client, session):
        _, _, org, _, lead, _ = _full_seed(session)

        resp = client.post(
            f"/api/v1/leads/{lead.id}/follow-ups",
            json={
                "channel": "phone",
                "result_category": "无效",
                "reason": "不需要服务",
            },
        )
        assert resp.status_code == 201

        session.refresh(lead)
        assert lead.lead_status == LeadStatus.BLOCKED

        block = session.exec(
            select(Blocklist).where(Blocklist.organization_id == org.id)
        ).first()
        assert block is not None
        assert block.reason == "不需要服务"

    def test_ac01_e1_lead_already_blocked_no_duplicate_blocklist(
        self, client, session
    ):
        _, _, org, _, lead, _ = _full_seed(session)
        lead.lead_status = LeadStatus.BLOCKED
        session.add(lead)
        session.add(Blocklist(organization_id=org.id, reason="不需要服务"))
        session.commit()

        resp = client.post(
            f"/api/v1/leads/{lead.id}/follow-ups",
            json={
                "channel": "phone",
                "result_category": "无效",
                "reason": "不需要服务",
            },
        )
        assert resp.status_code == 201

        blocks = session.exec(
            select(Blocklist).where(Blocklist.organization_id == org.id)
        ).all()
        assert len(blocks) == 1

    def test_ac01_b1_block_only_lead_without_organization(self, client, session):
        _, _, org, _, lead, _ = _full_seed(session)

        resp = client.post(
            f"/api/v1/leads/{lead.id}/follow-ups",
            json={
                "channel": "phone",
                "result_category": "无效",
                "reason": "不需要服务",
                "block_organization": False,
            },
        )
        assert resp.status_code == 201

        session.refresh(lead)
        assert lead.lead_status == LeadStatus.BLOCKED

        block = session.exec(
            select(Blocklist).where(Blocklist.organization_id == org.id)
        ).first()
        assert block is None


# ════════════════════════════════════════════════════════════════
# AC-02 / AC-03: Blocklist CRUD API
# ════════════════════════════════════════════════════════════════


class TestBlocklistCrud:
    def test_ac02_list_blocked_organizations(self, client, session, auth_headers):
        org1 = _seed_org(session, name="Org One")
        org2 = _seed_org(session, name="Org Two")
        session.add_all([
            Blocklist(organization_id=org1.id, reason="不需要服务"),
            Blocklist(organization_id=org2.id, reason="联系不上"),
        ])
        session.commit()

        resp = client.get("/api/v1/blocklist", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert {d["organization_id"] for d in data} == {str(org1.id), str(org2.id)}
        assert all("reason" in d and "created_at" in d for d in data)

    def test_ac02_e1_unauthorized_request(self, client, session):
        org = _seed_org(session)
        session.add(Blocklist(organization_id=org.id, reason="不需要服务"))
        session.commit()

        resp = client.get("/api/v1/blocklist")
        assert resp.status_code == 401

    def test_ac03_unblock_organization(self, client, session, auth_headers):
        _, _, org, _, lead, _ = _full_seed(session)
        lead.lead_status = LeadStatus.BLOCKED
        session.add(lead)
        block = Blocklist(organization_id=org.id, reason="不需要服务")
        session.add(block)
        session.commit()
        session.refresh(block)

        resp = client.delete(f"/api/v1/blocklist/{block.id}", headers=auth_headers)
        assert resp.status_code == 204

        assert (
            session.exec(select(Blocklist).where(Blocklist.id == block.id)).first()
            is None
        )

        session.refresh(lead)
        assert lead.lead_status == LeadStatus.NEW

    def test_ac03_e1_unblock_nonexistent_record(self, client, auth_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = client.delete(f"/api/v1/blocklist/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_ac03_b1_idempotent_unblock(self, client, session, auth_headers):
        org = _seed_org(session)
        block = Blocklist(organization_id=org.id, reason="不需要服务")
        session.add(block)
        session.commit()
        session.refresh(block)

        resp = client.delete(f"/api/v1/blocklist/{block.id}", headers=auth_headers)
        assert resp.status_code == 204

        resp = client.delete(f"/api/v1/blocklist/{block.id}", headers=auth_headers)
        assert resp.status_code == 404


# ════════════════════════════════════════════════════════════════
# AC-04: Lead Pool Excludes Blocked Leads by Default
# ════════════════════════════════════════════════════════════════


class TestLeadPoolExcludesBlocked:
    def test_ac04_blocked_leads_hidden_from_lead_pool(self, client, session):
        _full_seed(session, lead_status=LeadStatus.NEW)

        org2 = _seed_org(session, name="Org Two")
        doc2 = _seed_document(session, _seed_source(session, name="Source Two"))
        signal2 = _seed_signal(session, doc2, org2)
        lead2 = _seed_lead(session, org2, signal2, lead_status=LeadStatus.NEW)
        _seed_score(session, lead2)

        org3 = _seed_org(session, name="Org Three")
        doc3 = _seed_document(session, _seed_source(session, name="Source Three"))
        signal3 = _seed_signal(session, doc3, org3)
        lead3 = _seed_lead(session, org3, signal3, lead_status=LeadStatus.BLOCKED)
        _seed_score(session, lead3)

        resp = client.get("/api/v1/leads")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(d["lead_status"] != "blocked" for d in data)

    def test_ac04_e1_explicit_blocked_filter_shows_blocked(self, client, session):
        _, _, _, _, lead, _ = _full_seed(session, lead_status=LeadStatus.BLOCKED)

        resp = client.get("/api/v1/leads", params={"status": "blocked"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["lead_status"] == "blocked"

    def test_ac04_b1_blocked_leads_excluded_from_stats(self, client, session):
        # 5 leads: 4 new, 1 blocked
        for i in range(5):
            org = _seed_org(session, name=f"Org {i}")
            doc = _seed_document(session, _seed_source(session, name=f"Source {i}"))
            signal = _seed_signal(session, doc, org)
            status = LeadStatus.BLOCKED if i == 0 else LeadStatus.NEW
            lead = _seed_lead(session, org, signal, lead_status=status)
            _seed_score(session, lead)

        resp = client.get("/api/v1/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 4
