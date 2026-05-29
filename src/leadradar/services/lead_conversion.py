"""LeadConversionEngine — pure data transformation: Signal → Lead data.

No database sessions, no side effects.  All persistence lives in lead_service.py.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from leadradar.models import LeadStatus, Signal
from leadradar.schemas import ExtractionResult
from leadradar.scoring import score_lead
from leadradar.services.flag_derivation import FlagDerivationEngine, default_engine


@dataclass(frozen=True)
class OrganizationData:
    """Normalized, ready-to-persist organization fields."""

    name: str
    normalized_name: str
    province: str | None
    city: str | None
    county: str | None
    organization_type: str | None


@dataclass(frozen=True)
class LeadData:
    """Normalized, ready-to-persist lead fields."""

    customer_type: str | None
    recommended_package: str | None
    budget_bucket: str | None
    lead_status: LeadStatus


@dataclass(frozen=True)
class LeadScoreData:
    """Normalized, ready-to-persist lead_score fields."""

    total_score: int
    grade: str
    budget_strength_score: int
    scenario_fit_score: int
    timing_score: int
    reachability_score: int
    leverage_score: int
    score_reason_json: str


@dataclass(frozen=True)
class LeadConversionResult:
    """Complete output of the pure conversion step."""

    organization_data: OrganizationData
    lead_data: LeadData
    lead_score_data: LeadScoreData


class LeadConversionEngine:
    """Pure business-logic engine: Signal + ExtractionResult → Lead data.

    The engine never touches a database.  It produces *data* that the caller
    is responsible for persisting (and deduplicating, e.g. organisations by
    ``normalized_name``).
    """

    def __init__(self, flag_engine: FlagDerivationEngine | None = None) -> None:
        self._flag_engine = flag_engine or default_engine()

    # ── public interface ────────────────────────────────────────────

    def convert(
        self,
        signal: Signal,
        extraction_result: ExtractionResult | None,
    ) -> LeadConversionResult:
        """Derive all lead-related data from a Signal and its extraction."""
        org_data = self._derive_organization_data(extraction_result)
        scoring_input = self._flag_engine.derive(signal, extraction_result)
        scoring_result = score_lead(scoring_input)
        lead_data = self._derive_lead_data(extraction_result, signal.budget_amount)
        score_data = self._derive_lead_score_data(scoring_result)
        return LeadConversionResult(
            organization_data=org_data,
            lead_data=lead_data,
            lead_score_data=score_data,
        )

    # ── private derivations ─────────────────────────────────────────

    @staticmethod
    def _derive_organization_data(
        extraction_result: ExtractionResult | None,
    ) -> OrganizationData:
        """Build OrganisationData from extraction result fields."""
        org_name = (
            extraction_result.organization_name.strip()
            if extraction_result and extraction_result.organization_name
            else ""
        )
        if not org_name:
            org_name = "未知机构"

        region = extraction_result.region if extraction_result else None

        return OrganizationData(
            name=org_name,
            normalized_name=org_name.lower(),
            province=region.province if region else None,
            city=region.city if region else None,
            county=region.county if region else None,
            organization_type=extraction_result.customer_type if extraction_result else None,
        )

    @staticmethod
    def _derive_lead_data(
        extraction_result: ExtractionResult | None,
        budget_amount: float | None,
    ) -> LeadData:
        """Build LeadData from extraction result and raw signal fields."""
        recommended = (
            extraction_result.product_fit[0]
            if extraction_result and extraction_result.product_fit
            else None
        )
        return LeadData(
            customer_type=extraction_result.customer_type if extraction_result else None,
            recommended_package=recommended,
            budget_bucket=_budget_bucket(budget_amount),
            lead_status=LeadStatus.NEW,
        )

    @staticmethod
    def _derive_lead_score_data(
        scoring_result,
    ) -> LeadScoreData:
        """Build LeadScoreData from a LeadScoringResult."""
        return LeadScoreData(
            total_score=scoring_result.total_score,
            grade=scoring_result.grade,
            budget_strength_score=scoring_result.breakdown["budget_strength"],
            scenario_fit_score=scoring_result.breakdown["scenario_fit"],
            timing_score=scoring_result.breakdown["timing"],
            reachability_score=scoring_result.breakdown["reachability"],
            leverage_score=scoring_result.breakdown["leverage"],
            score_reason_json=json.dumps(scoring_result.reasons, ensure_ascii=False),
        )


# ── helpers (also pure) ───────────────────────────────────────────


def _budget_bucket(amount: float | None) -> str | None:
    if amount is None:
        return None
    if amount < 100_000:
        return "<10万"
    if amount < 500_000:
        return "10-50万"
    if amount < 1_000_000:
        return "50-100万"
    if amount < 5_000_000:
        return "100-500万"
    return ">500万"
