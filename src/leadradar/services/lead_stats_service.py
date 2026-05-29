"""Lead stats service — aggregations, distributions, weekly reports."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlmodel import Session, select

from leadradar.api.schemas import DistributionItem, StatsOut, WeeklyReport
from leadradar.models import FollowUp, Lead
from leadradar.repositories.lead_repo import LeadRepository


class LeadStatsService:
    """Service for statistical aggregations over leads.

    All distribution, counting, and reporting logic lives here so that
    routes.py does not build ad-hoc aggregations.
    """

    def __init__(self, repo: LeadRepository | None = None):
        self._repo = repo or LeadRepository()

    def get_stats(self, session: Session) -> StatsOut:
        """Return high-level statistics and distributions."""
        rows = self._repo.list_with_relations(session, limit=10_000, offset=0)

        total = len(rows)
        sa_count = sum(1 for r in rows if r.score.grade in ("S", "A"))
        pending = sum(
            1 for r in rows if r.lead.lead_status.value in ("new", "qualified")
        )
        scheduled = sum(
            1 for r in rows if r.lead.lead_status.value == "diagnosis_scheduled"
        )
        invalid = sum(1 for r in rows if r.lead.lead_status.value == "invalid")
        invalid_rate = f"{(invalid / total * 100):.1f}" if total > 0 else "0"

        return StatsOut(
            total=total,
            sa_count=sa_count,
            pending=pending,
            scheduled=scheduled,
            invalid=invalid,
            invalid_rate=invalid_rate,
            signal_type_distribution=self._distribution(
                rows, lambda r: r.signal.signal_type if r.signal else "unknown"
            )[:8],
            package_distribution=self._distribution(
                rows, lambda r: r.lead.recommended_package or "未分类"
            ),
            province_distribution=self._distribution(
                rows, lambda r: r.org.province or "未知"
            )[:8],
        )

    def get_weekly_report(self, session: Session) -> WeeklyReport:
        """Return the weekly activity summary."""
        one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

        leads = session.exec(
            select(Lead).where(Lead.created_at >= one_week_ago)
        ).all()
        follow_ups = session.exec(
            select(FollowUp).where(FollowUp.created_at >= one_week_ago)
        ).all()

        new_leads = len(leads)
        followed_up = len(follow_ups)
        contacted = sum(
            1 for lead in leads if lead.lead_status.value in ("called", "connected")
        )
        scheduled = sum(
            1 for lead in leads if lead.lead_status.value == "diagnosis_scheduled"
        )
        won = sum(1 for lead in leads if lead.lead_status.value == "won")
        lost = sum(1 for lead in leads if lead.lead_status.value == "lost")

        total_outcomes = won + lost
        conversion_rate = f"{(won / total_outcomes * 100):.0f}%" if total_outcomes > 0 else "N/A"

        return WeeklyReport(
            new_leads=new_leads,
            followed_up=followed_up,
            contacted=contacted,
            scheduled=scheduled,
            won=won,
            lost=lost,
            conversion_rate=conversion_rate,
        )

    @staticmethod
    def _distribution(
        rows: list, key_fn: Callable
    ) -> list[DistributionItem]:
        """Count occurrences by a key function and return sorted DistributionItems."""
        counts: dict[str, int] = {}
        for row in rows:
            k = key_fn(row)
            counts[k] = counts.get(k, 0) + 1
        return [
            DistributionItem(name=k, count=v)
            for k, v in sorted(counts.items(), key=lambda x: -x[1])
        ]
