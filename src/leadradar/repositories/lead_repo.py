"""Lead repository — encapsulates the repeated Lead+Score+Org+Signal JOIN query."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from sqlmodel import Session, select

from leadradar.models import Lead, LeadScore, Organization, Signal


@dataclass
class LeadListRow:
    """A complete lead with all related entities.

    This DTO hides the JOIN structure from callers.  Service layers
    extract only the fields they need.
    """

    lead: Lead
    score: LeadScore
    org: Organization
    signal: Signal | None


class LeadRepository:
    """Repository for lead-centric queries.

    Interface surface:
      - list_with_relations(session, filters) -> list[LeadListRow]
      - get_by_id(session, lead_id) -> LeadListRow | None

    All JOIN logic lives here so that routes.py never builds a
    select().join() query by hand.
    """

    def _base_query(self):
        """Return the common four-table JOIN."""
        return (
            select(Lead, LeadScore, Organization, Signal)
            .join(LeadScore, LeadScore.lead_id == Lead.id)
            .join(Organization, Organization.id == Lead.organization_id)
            .outerjoin(Signal, Signal.id == Lead.primary_signal_id)
        )

    def list_with_relations(
        self,
        session: Session,
        *,
        grade: str | None = None,
        status: str | None = None,
        signal_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
        order_by: Literal["created_at_desc"] = "created_at_desc",
    ) -> list[LeadListRow]:
        """Fetch leads with all relations, applying optional filters."""
        query = self._base_query()

        if grade:
            query = query.where(LeadScore.grade == grade.upper())
        if status:
            query = query.where(Lead.lead_status == status)
        if signal_type:
            query = query.where(Signal.signal_type == signal_type)

        query = query.order_by(Lead.created_at.desc())
        query = query.offset(offset).limit(limit)

        results = session.exec(query).all()
        return [
            LeadListRow(lead=lead, score=score, org=org, signal=signal)
            for lead, score, org, signal in results
        ]

    def get_by_id(self, session: Session, lead_id: UUID) -> LeadListRow | None:
        """Fetch a single lead with all relations by ID."""
        query = self._base_query().where(Lead.id == lead_id)
        result = session.exec(query).first()
        if result is None:
            return None
        lead, score, org, signal = result
        return LeadListRow(lead=lead, score=score, org=org, signal=signal)
