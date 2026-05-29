"""Lead query service — read-only operations for leads, details, lists."""

from __future__ import annotations

from uuid import UUID

from sqlmodel import Session

from leadradar.api.schemas import (
    CallScript,
    LeadDetail,
    LeadListItem,
    OrganizationBrief,
    ScoreBrief,
    SignalBrief,
)
from leadradar.models import LeadStatus
from leadradar.repositories.lead_repo import LeadListRow, LeadRepository
from leadradar.services.call_script import generate_call_script as _gen_script


class LeadQueryService:
    """Service for lead read operations.

    Sits between the route layer (HTTP) and the repository layer (DB).
    Responsible for:
      - Translating repository rows into API response schemas
      - Orchestrating related data for detail views (e.g. call scripts)
    """

    def __init__(self, repo: LeadRepository | None = None):
        self._repo = repo or LeadRepository()

    def list_leads(
        self,
        session: Session,
        *,
        grade: str | None = None,
        status: str | None = None,
        signal_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LeadListItem]:
        """Return a paginated list of leads for the list view."""
        rows = self._repo.list_with_relations(
            session,
            grade=grade,
            status=status,
            signal_type=signal_type,
            limit=limit,
            offset=offset,
        )
        return [self._to_list_item(r) for r in rows]

    def get_lead_detail(self, session: Session, lead_id: UUID) -> LeadDetail | None:
        """Return full lead detail including score, org, signal, and call script."""
        row = self._repo.get_by_id(session, lead_id)
        if row is None:
            return None
        return self._to_detail(row)

    @staticmethod
    def _to_list_item(row: LeadListRow) -> LeadListItem:
        """Map a LeadListRow to the API list-item schema."""
        lead = row.lead
        score = row.score
        org = row.org
        signal = row.signal

        status_value = (
            lead.lead_status.value
            if isinstance(lead.lead_status, LeadStatus)
            else str(lead.lead_status)
        )

        return LeadListItem(
            id=lead.id,
            organization_name=org.name,
            customer_type=lead.customer_type,
            recommended_package=lead.recommended_package,
            budget_bucket=lead.budget_bucket,
            signal_type=signal.signal_type if signal else None,
            province=org.province,
            lead_status=status_value,
            total_score=score.total_score,
            grade=score.grade,
            created_at=lead.created_at,
        )

    def _to_detail(self, row: LeadListRow) -> LeadDetail:
        """Map a LeadListRow to the full LeadDetail schema."""
        lead = row.lead
        score = row.score
        org = row.org
        signal = row.signal

        status_value = (
            lead.lead_status.value
            if isinstance(lead.lead_status, LeadStatus)
            else str(lead.lead_status)
        )

        script_data = _gen_script(
            customer_type=lead.customer_type,
            organization_name=org.name,
            signal_title=signal.title if signal else None,
            signal_type=signal.signal_type if signal else None,
            recommended_package=lead.recommended_package,
            budget_amount=signal.budget_amount if signal else None,
        )

        return LeadDetail(
            id=lead.id,
            organization=OrganizationBrief(
                id=org.id,
                name=org.name,
                province=org.province,
                city=org.city,
                county=org.county,
                organization_type=org.organization_type,
            ),
            signal=SignalBrief(
                id=signal.id,
                signal_type=signal.signal_type,
                title=signal.title,
                budget_amount=signal.budget_amount,
                source_url=signal.source_url,
                evidence_text=signal.evidence_text,
                confidence=signal.confidence,
                created_at=signal.created_at,
            ) if signal else SignalBrief(
                id=lead.primary_signal_id or lead.id,
                signal_type="unknown",
                title=None,
                budget_amount=None,
                source_url=None,
                evidence_text=None,
                confidence=0.0,
                created_at=lead.created_at,
            ),
            score=ScoreBrief(
                total_score=score.total_score,
                grade=score.grade,
                budget_strength_score=score.budget_strength_score,
                scenario_fit_score=score.scenario_fit_score,
                timing_score=score.timing_score,
                reachability_score=score.reachability_score,
                leverage_score=score.leverage_score,
            ),
            call_script=CallScript(**script_data),
            customer_type=lead.customer_type,
            recommended_package=lead.recommended_package,
            budget_bucket=lead.budget_bucket,
            lead_status=status_value,
            owner=lead.owner,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
        )
