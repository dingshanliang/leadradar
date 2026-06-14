"""Blacklist service — block/unblock organizations and leads."""

from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from leadradar.models import Blocklist, Lead, LeadStatus


class BlacklistService:
    """Service for managing the blocklist and related lead status transitions."""

    def block_lead_and_organization(
        self,
        session: Session,
        lead: Lead,
        reason: str,
        block_organization: bool = True,
    ) -> Blocklist | None:
        """Mark a lead as blocked and optionally block its organization."""
        lead.lead_status = LeadStatus.BLOCKED
        session.add(lead)

        if not block_organization or lead.organization_id is None:
            session.commit()
            return None

        existing = session.exec(
            select(Blocklist).where(Blocklist.organization_id == lead.organization_id)
        ).first()
        if existing:
            session.commit()
            return existing

        block = Blocklist(organization_id=lead.organization_id, reason=reason)
        session.add(block)
        session.commit()
        session.refresh(block)
        return block

    def unblock_organization(self, session: Session, block_id: UUID) -> bool:
        """Remove a blocklist record and restore blocked leads to new.

        Returns True if the record existed and was removed, False otherwise.
        """
        block = session.get(Blocklist, block_id)
        if not block:
            return False

        org_id = block.organization_id
        session.delete(block)
        session.commit()

        if org_id:
            leads = session.exec(
                select(Lead).where(
                    Lead.organization_id == org_id,
                    Lead.lead_status == LeadStatus.BLOCKED,
                )
            ).all()
            for lead in leads:
                lead.lead_status = LeadStatus.NEW
                session.add(lead)
            session.commit()

        return True

    def list_blocklist(self, session: Session) -> list[Blocklist]:
        """Return all blocklist records ordered by creation time."""
        return list(
            session.exec(select(Blocklist).order_by(Blocklist.created_at.desc())).all()
        )
