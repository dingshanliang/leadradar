"""Tests for LeadQueryService, LeadStatsService, and LeadExportService."""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine

from leadradar.adapters.export_adapters import CsvExportAdapter, XlsxExportAdapter
from leadradar.models import (
    FollowUp,
    Lead,
    LeadScore,
    LeadStatus,
    Organization,
    Signal,
)
from leadradar.repositories.lead_repo import LeadRepository
from leadradar.services.lead_export_service import LeadExportService
from leadradar.services.lead_query_service import LeadQueryService
from leadradar.services.lead_stats_service import LeadStatsService


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


def _seed_org(session, name="测试机构"):
    org = Organization(name=name, normalized_name=name.lower(), province="江西")
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


def _seed_signal(session, org, **kwargs):
    defaults = {
        "organization_id": org.id,
        "signal_type": "procurement_intent",
        "title": "测试项目",
        "budget_amount": 1800000,
        "confidence": 0.92,
        "source_url": "https://example.gov.cn/1",
        "evidence_text": "预算：180万元",
    }
    defaults.update(kwargs)
    signal = Signal(**defaults)
    session.add(signal)
    session.commit()
    session.refresh(signal)
    return signal


def _seed_lead(session, org, signal, status=LeadStatus.NEW, grade="S", **kwargs):
    defaults = {
        "organization_id": org.id,
        "primary_signal_id": signal.id,
        "customer_type": "region_brand_government",
        "recommended_package": "区域品牌数字化管理包",
        "budget_bucket": "100-500万",
        "lead_status": status,
    }
    defaults.update(kwargs)
    lead = Lead(**defaults)
    session.add(lead)
    session.commit()
    session.refresh(lead)

    score = LeadScore(
        lead_id=lead.id,
        total_score=92 if grade == "S" else 65,
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


# ════════════════════════════════════════════════════════════════
# LeadQueryService
# ════════════════════════════════════════════════════════════════


class TestLeadQueryService:
    def test_list_leads_maps_to_list_items(self, session, repo):
        org = _seed_org(session)
        signal = _seed_signal(session, org)
        lead, score = _seed_lead(session, org, signal)

        svc = LeadQueryService(repo=repo)
        items = svc.list_leads(session)

        assert len(items) == 1
        assert str(items[0].id) == str(lead.id)
        assert items[0].organization_name == org.name
        assert items[0].grade == "S"
        assert items[0].lead_status == "new"

    def test_list_leads_applies_filters(self, session, repo):
        org = _seed_org(session)
        signal = _seed_signal(session, org)
        _seed_lead(session, org, signal, grade="S")
        _seed_lead(session, org, signal, grade="A")

        svc = LeadQueryService(repo=repo)
        items = svc.list_leads(session, grade="S")
        assert len(items) == 1
        assert items[0].grade == "S"

    def test_get_lead_detail_returns_full_detail(self, session, repo):
        org = _seed_org(session)
        signal = _seed_signal(session, org)
        lead, score = _seed_lead(session, org, signal)

        svc = LeadQueryService(repo=repo)
        detail = svc.get_lead_detail(session, lead.id)

        assert detail is not None
        assert str(detail.id) == str(lead.id)
        assert detail.organization.name == org.name
        assert detail.score.total_score == score.total_score
        assert detail.call_script.opening is not None
        assert len(detail.call_script.questions) > 0

    def test_get_lead_detail_not_found(self, session, repo):
        from uuid import uuid4
        svc = LeadQueryService(repo=repo)
        detail = svc.get_lead_detail(session, uuid4())
        assert detail is None


# ════════════════════════════════════════════════════════════════
# LeadStatsService
# ════════════════════════════════════════════════════════════════


class TestLeadStatsService:
    def test_get_stats_counts_correctly(self, session, repo):
        org = _seed_org(session)
        signal = _seed_signal(session, org)
        _seed_lead(session, org, signal, grade="S", status=LeadStatus.NEW)
        _seed_lead(session, org, signal, grade="A", status=LeadStatus.CALLED)
        _seed_lead(session, org, signal, grade="D", status=LeadStatus.INVALID)

        svc = LeadStatsService(repo=repo)
        stats = svc.get_stats(session)

        assert stats.total == 3
        assert stats.sa_count == 2
        assert stats.pending == 1  # new
        assert stats.invalid == 1
        assert stats.invalid_rate == "33.3"

    def test_get_stats_distributions(self, session, repo):
        org = _seed_org(session, name="机构A")
        org2 = _seed_org(session, name="机构B")
        org2.province = "广东"
        session.add(org2)
        session.commit()

        signal = _seed_signal(session, org)
        signal2 = _seed_signal(session, org2, signal_type="tender_notice")
        _seed_lead(session, org, signal, recommended_package="包A")
        _seed_lead(session, org2, signal2, recommended_package="包B")

        svc = LeadStatsService(repo=repo)
        stats = svc.get_stats(session)

        provinces = {d.name: d.count for d in stats.province_distribution}
        assert provinces.get("江西") == 1
        assert provinces.get("广东") == 1

    def test_get_weekly_report(self, session, repo):
        from datetime import datetime, timezone

        org = _seed_org(session)
        signal = _seed_signal(session, org)
        lead, _ = _seed_lead(session, org, signal, status=LeadStatus.WON)

        follow_up = FollowUp(
            lead_id=lead.id,
            channel="phone",
            result="已成交",
            created_at=datetime.now(timezone.utc),
        )
        session.add(follow_up)
        session.commit()

        svc = LeadStatsService(repo=repo)
        report = svc.get_weekly_report(session)

        assert report.new_leads >= 1
        assert report.followed_up >= 1
        assert report.won >= 1


# ════════════════════════════════════════════════════════════════
# LeadExportService
# ════════════════════════════════════════════════════════════════


class TestLeadExportService:
    def test_build_export_rows(self, session, repo):
        org = _seed_org(session)
        signal = _seed_signal(session, org)
        lead, _ = _seed_lead(session, org, signal)

        svc = LeadExportService(repo=repo)
        rows = svc.build_export_rows(session)

        assert len(rows) == 1
        assert rows[0]["organization_name"] == org.name
        assert rows[0]["grade"] == "S"
        assert rows[0]["budget_amount"] == 1800000
        assert rows[0]["signal_type"] == "procurement_intent"

    def test_export_rows_filter_by_grade(self, session, repo):
        org = _seed_org(session)
        signal = _seed_signal(session, org)
        _seed_lead(session, org, signal, grade="S")
        _seed_lead(session, org, signal, grade="A")

        svc = LeadExportService(repo=repo)
        rows = svc.build_export_rows(session, grade="S")
        assert len(rows) == 1
        assert rows[0]["grade"] == "S"


# ════════════════════════════════════════════════════════════════
# ExportAdapters
# ════════════════════════════════════════════════════════════════


class TestCsvExportAdapter:
    def test_render_csv_with_header(self):
        adapter = CsvExportAdapter()
        rows = [
            {
                "organization_name": "机构A",
                "lead_status": "new",
                "grade": "S",
                "total_score": 92,
                "customer_type": "gov",
                "recommended_package": "包A",
                "budget_bucket": "100-500万",
                "signal_type": "procurement_intent",
                "budget_amount": 1800000,
                "source_url": "https://example.gov.cn/1",
                "evidence_text": "预算180万元",
            }
        ]
        content = adapter.render(rows)
        assert "organization_name" in content
        assert "机构A" in content
        assert "S" in content

    def test_empty_rows(self):
        adapter = CsvExportAdapter()
        content = adapter.render([])
        assert "organization_name" in content  # header only


class TestXlsxExportAdapter:
    def test_render_xlsx(self):
        adapter = XlsxExportAdapter()
        rows = [
            {
                "organization_name": "机构A",
                "lead_status": "new",
                "grade": "S",
                "total_score": 92,
                "customer_type": "gov",
                "recommended_package": "包A",
                "budget_bucket": "100-500万",
                "signal_type": "procurement_intent",
                "budget_amount": 1800000,
                "source_url": "https://example.gov.cn/1",
                "evidence_text": "预算180万元",
            }
        ]
        content = adapter.render(rows)
        assert isinstance(content, bytes)
        assert len(content) > 0

    def test_content_type_and_filename(self):
        adapter = XlsxExportAdapter()
        assert "spreadsheetml" in adapter.content_type()
        assert adapter.filename() == "leads.xlsx"
