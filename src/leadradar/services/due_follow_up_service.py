"""Service for querying follow-ups that are due (past or within the next N days)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, func, select

from leadradar.api.schemas import DueFollowUp
from leadradar.models import FollowUp, Lead, LeadStatus, Organization

_TERMINAL_STATUSES = {
    LeadStatus.WON,
    LeadStatus.LOST,
    LeadStatus.INVALID,
    LeadStatus.BLOCKED,
}

_TERMINAL_STATUS_VALUES = [s.value for s in _TERMINAL_STATUSES]


class DueFollowUpService:
    """Return follow-ups whose ``next_action_at`` has passed or is approaching."""

    DEFAULT_WINDOW_DAYS = 7
    DEFAULT_LIMIT = 50

    def _upper_bound(self, window_days: int) -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=window_days)

    def _base_query(self, window_days: int):
        upper_bound = self._upper_bound(window_days)
        return (
            select(FollowUp, Lead, Organization)
            .join(Lead, Lead.id == FollowUp.lead_id)  # type: ignore[arg-type]
            .join(Organization, Organization.id == Lead.organization_id)  # type: ignore[arg-type]
            .where(FollowUp.next_action_at.is_not(None))  # type: ignore[union-attr]
            .where(FollowUp.next_action_at <= upper_bound)  # type: ignore[operator]
            .where(Lead.lead_status.not_in(_TERMINAL_STATUS_VALUES))  # type: ignore[attr-defined]
        )

    def list_due_follow_ups(
        self,
        session: Session,
        *,
        window_days: int = DEFAULT_WINDOW_DAYS,
        limit: int = DEFAULT_LIMIT,
    ) -> list[DueFollowUp]:
        rows = session.exec(
            self._base_query(window_days)
            .order_by(FollowUp.next_action_at.asc())  # type: ignore[union-attr]
            .limit(limit)
        ).all()
        return [
            DueFollowUp(
                follow_up_id=fu.id,
                lead_id=fu.lead_id,
                organization_name=org.name,
                next_action_at=fu.next_action_at,
                result=fu.result,
            )
            for fu, _lead, org in rows
        ]

    def count_due_follow_ups(
        self,
        session: Session,
        *,
        window_days: int = DEFAULT_WINDOW_DAYS,
    ) -> int:
        upper_bound = self._upper_bound(window_days)
        count = session.exec(
            select(func.count(FollowUp.id))  # type: ignore[arg-type]
            .join(Lead, Lead.id == FollowUp.lead_id)  # type: ignore[arg-type]
            .where(FollowUp.next_action_at.is_not(None))  # type: ignore[union-attr]
            .where(FollowUp.next_action_at <= upper_bound)  # type: ignore[operator]
            .where(Lead.lead_status.not_in(_TERMINAL_STATUS_VALUES))  # type: ignore[attr-defined]
        ).one()
        return int(count)
