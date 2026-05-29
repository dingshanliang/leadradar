"""Tests for LeadRepository — the consolidated JOIN query seam."""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine

from leadradar.models import Lead, LeadScore, LeadStatus, Organization, RawDocument, Signal, Source
from leadradar.repositories.lead_repo import LeadListRow, LeadRepository


@pytest.fixture
def engine():
    e = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(e)
    return e


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def repo():
    return LeadRepository()


def _seed_source(session):
    source = Source(name="测试源", source_type="test")
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


def _seed_org(session, name="测试机构"):
    org = Organization(name=name, normalized_name=name.lower(), province="江西")
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


def _seed_document(session, source):
    doc = RawDocument(
        source_id=source.id,
        url="https://example.gov.cn/1",
        title="测试公告",
        extracted_text="测试内容",
        parse_status="completed",
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def _seed_signal(session, doc, org, signal_type="procurement_intent"):
    signal = Signal(
        raw_document_id=doc.id,
        organization_id=org.id,
        signal_type=signal_type,
        title="测试项目",
        budget_amount=1800000,
        confidence=0.92,
        source_url=doc.url,
        evidence_text="预算：180万元",
    )
    session.add(signal)
    session.commit()
    session.refresh(signal)
    return signal


def _seed_lead(session, org, signal, status=LeadStatus.NEW, grade="S"):
    lead = Lead(
        organization_id=org.id,
        primary_signal_id=signal.id,
        customer_type="region_brand_government",
        recommended_package="区域品牌数字化管理包",
        budget_bucket="100-500万",
        lead_status=status,
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)

    score = LeadScore(
        lead_id=lead.id,
        total_score=92,
        grade=grade,
        budget_strength_score=35,
        scenario_fit_score=22,
        timing_score=20,
        reachability_score=10,
        leverage_score=5,
    )
    session.add(score)
    session.commit()
    return lead, score


def _full_seed(session):
    source = _seed_source(session)
    doc = _seed_document(session, source)
    org = _seed_org(session)
    signal = _seed_signal(session, doc, org)
    lead, score = _seed_lead(session, org, signal)
    return lead, score, org, signal


class TestLeadRepositoryListWithRelations:
    def test_returns_complete_rows(self, session, repo):
        _full_seed(session)
        rows = repo.list_with_relations(session)
        assert len(rows) == 1
        row = rows[0]
        assert isinstance(row, LeadListRow)
        assert row.org.name == "测试机构"
        assert row.score.grade == "S"

    def test_filters_by_grade(self, session, repo):
        source = _seed_source(session)
        doc = _seed_document(session, source)
        org = _seed_org(session)
        signal = _seed_signal(session, doc, org)
        _seed_lead(session, org, signal, grade="S")
        _seed_lead(session, org, signal, grade="A")

        rows = repo.list_with_relations(session, grade="S")
        assert len(rows) == 1
        assert rows[0].score.grade == "S"

    def test_filters_by_status(self, session, repo):
        source = _seed_source(session)
        doc = _seed_document(session, source)
        org = _seed_org(session)
        signal = _seed_signal(session, doc, org)
        _seed_lead(session, org, signal, status=LeadStatus.NEW)
        _seed_lead(session, org, signal, status=LeadStatus.CALLED)

        rows = repo.list_with_relations(session, status="new")
        assert len(rows) == 1
        assert rows[0].lead.lead_status == LeadStatus.NEW

    def test_pagination_limit_offset(self, session, repo):
        source = _seed_source(session)
        doc = _seed_document(session, source)
        org = _seed_org(session)
        signal = _seed_signal(session, doc, org)
        for i in range(5):
            _seed_lead(session, org, signal, grade="S")

        rows = repo.list_with_relations(session, limit=2, offset=0)
        assert len(rows) == 2

        rows = repo.list_with_relations(session, limit=2, offset=2)
        assert len(rows) == 2

        rows = repo.list_with_relations(session, limit=2, offset=4)
        assert len(rows) == 1

    def test_orders_by_created_at_desc(self, session, repo):
        source = _seed_source(session)
        doc = _seed_document(session, source)
        org = _seed_org(session)
        signal = _seed_signal(session, doc, org)
        lead1, _ = _seed_lead(session, org, signal)
        lead2, _ = _seed_lead(session, org, signal)

        rows = repo.list_with_relations(session)
        # lead2 was created after lead1
        assert rows[0].lead.id == lead2.id
        assert rows[1].lead.id == lead1.id

    def test_empty_result(self, session, repo):
        rows = repo.list_with_relations(session)
        assert rows == []


class TestLeadRepositoryGetById:
    def test_returns_row_when_found(self, session, repo):
        lead, _, org, signal = _full_seed(session)
        row = repo.get_by_id(session, lead.id)
        assert row is not None
        assert row.lead.id == lead.id
        assert row.org.name == org.name
        assert row.signal.id == signal.id

    def test_returns_none_when_not_found(self, session, repo):
        from uuid import uuid4
        row = repo.get_by_id(session, uuid4())
        assert row is None
