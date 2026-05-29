"""Lead export service — prepares data rows for file export."""

from __future__ import annotations

from sqlmodel import Session

from leadradar.models import LeadStatus
from leadradar.repositories.lead_repo import LeadListRow, LeadRepository


class LeadExportService:
    """Service for preparing lead data in export-friendly dict format.

    Separates field extraction (business logic) from format rendering (adapters).
    """

    def __init__(self, repo: LeadRepository | None = None):
        self._repo = repo or LeadRepository()

    def build_export_rows(
        self, session: Session, *, grade: str | None = None
    ) -> list[dict[str, object]]:
        """Fetch leads and map them to flat dicts suitable for CSV/XLSX export."""
        rows = self._repo.list_with_relations(
            session, grade=grade, limit=10_000, offset=0
        )
        return [self._to_export_dict(r) for r in rows]

    @staticmethod
    def _to_export_dict(row: LeadListRow) -> dict[str, object]:
        lead = row.lead
        score = row.score
        org = row.org
        signal = row.signal

        status_value = (
            lead.lead_status.value
            if isinstance(lead.lead_status, LeadStatus)
            else str(lead.lead_status)
        )

        return {
            "organization_name": org.name,
            "lead_status": status_value,
            "grade": score.grade,
            "total_score": score.total_score,
            "customer_type": lead.customer_type or "",
            "recommended_package": lead.recommended_package or "",
            "budget_bucket": lead.budget_bucket or "",
            "signal_type": signal.signal_type if signal else "",
            "budget_amount": signal.budget_amount if signal else "",
            "source_url": signal.source_url if signal else "",
            "evidence_text": signal.evidence_text if signal else "",
        }
