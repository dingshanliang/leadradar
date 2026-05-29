"""FlagDerivationEngine — pure derivation logic for scoring flags.

Each rule is a small, testable function (Signal, ExtractionResult|None) -> bool.
Rules are registered with (dimension, flag_name, rule_fn) and validated
against ScoringRuleSet at registration time so a typo in a flag name
fails fast on import, not silently at runtime.
"""

from __future__ import annotations

from typing import Callable

from leadradar.models import Signal
from leadradar.schemas import ExtractionResult, LeadScoringInput
from leadradar.services.scoring_rule_set import ScoringRuleSet

FlagRule = Callable[[Signal, ExtractionResult | None], bool]


class FlagDerivationEngine:
    """Derive scoring flags from Signal + ExtractionResult.

    Usage:
        engine = default_engine()
        scoring_input = engine.derive(signal, extraction_result)
    """

    def __init__(self, rule_set: ScoringRuleSet | None = None):
        self._rule_set = rule_set or ScoringRuleSet()
        self._rules: list[tuple[str, str, FlagRule]] = []

    def register(
        self,
        dimension: str,
        flag_name: str,
        rule: FlagRule,
    ) -> None:
        """Register a derivation rule.

        Args:
            dimension: One of the five scoring dimensions.
            flag_name: Must exist in the YAML rule set for that dimension.
            rule: Pure function that returns True when the flag should fire.

        Raises:
            ValueError: If dimension or flag_name is not known to the rule set.
        """
        if dimension not in self._rule_set.dimensions():
            raise ValueError(
                f"Unknown dimension '{dimension}'. "
                f"Valid: {self._rule_set.dimensions()}"
            )
        if not self._rule_set.has_flag(dimension, flag_name):
            raise ValueError(
                f"Unknown flag '{flag_name}' for dimension '{dimension}'. "
                f"Valid flags: {self._rule_set.valid_flags_for(dimension)}"
            )
        self._rules.append((dimension, flag_name, rule))

    def derive(
        self,
        signal: Signal,
        result: ExtractionResult | None,
    ) -> LeadScoringInput:
        """Derive LeadScoringInput by running all registered rules."""
        flags_by_dimension: dict[str, list[str]] = {
            dim: [] for dim in self._rule_set.dimensions()
        }

        for dimension, flag_name, rule in self._rules:
            try:
                if rule(signal, result):
                    flags_by_dimension[dimension].append(flag_name)
            except Exception:
                # A single rule failure should not break the whole derivation.
                # In production this would be logged.
                continue

        return LeadScoringInput(
            signal_type=signal.signal_type,
            scenario_flags=flags_by_dimension["scenario_fit"],
            timing_flags=flags_by_dimension["timing"],
            reachability_flags=flags_by_dimension["reachability"],
            leverage_flags=flags_by_dimension["leverage"],
        )


# ════════════════════════════════════════════════════════════════
# Scenario-fit rules
# ════════════════════════════════════════════════════════════════


def _region_brand_or_association(
    _signal: Signal, result: ExtractionResult | None
) -> bool:
    if not result:
        return False
    return result.customer_type in ("region_brand_government", "region_brand_association")


def _prepackaged_food(_signal: Signal, result: ExtractionResult | None) -> bool:
    if not result:
        return False
    need = result.need_summary or ""
    return "食品" in need or "预包装" in need


def _agri_product_brand(_signal: Signal, result: ExtractionResult | None) -> bool:
    if not result:
        return False
    need = result.need_summary or ""
    keywords = " ".join(result.matched_keywords)
    return "农产品" in need or "农产品" in keywords


def _gift_box_or_packaged_product(
    _signal: Signal, result: ExtractionResult | None
) -> bool:
    if not result:
        return False
    return "包装" in (result.need_summary or "")


def _certification_or_gi(_signal: Signal, result: ExtractionResult | None) -> bool:
    if not result:
        return False
    keywords = " ".join(result.matched_keywords)
    return any(k in keywords for k in ("地理标志", "名特优新"))


def _poor_existing_qr(_signal: Signal, result: ExtractionResult | None) -> bool:
    if not result:
        return False
    need = result.need_summary or ""
    return "二维码" in need and "体验" in need


# ════════════════════════════════════════════════════════════════
# Timing rules
# ════════════════════════════════════════════════════════════════


def _procurement_expected_within_3_months(
    _signal: Signal, result: ExtractionResult | None
) -> bool:
    if not result:
        return False
    return result.signal_type == "procurement_intent"


def _newly_published_tender(
    _signal: Signal, result: ExtractionResult | None
) -> bool:
    if not result:
        return False
    return result.signal_type == "tender_notice"


def _newly_won_project(_signal: Signal, result: ExtractionResult | None) -> bool:
    if not result:
        return False
    return result.signal_type == "winning_notice"


# ════════════════════════════════════════════════════════════════
# Leverage rules
# ════════════════════════════════════════════════════════════════


def _multi_org_region_brand_project(
    _signal: Signal, result: ExtractionResult | None
) -> bool:
    if not result:
        return False
    return "区域品牌数字化管理包" in result.product_fit


def _packaging_or_printing_partner(
    _signal: Signal, result: ExtractionResult | None
) -> bool:
    if not result:
        return False
    return any(p in result.product_fit for p in ("渠道白标工具包",))


# ════════════════════════════════════════════════════════════════
# Reachability rules (mutually exclusive — only one should fire)
# ════════════════════════════════════════════════════════════════


def _agency_phone(signal: Signal, _result: ExtractionResult | None) -> bool:
    text = signal.evidence_text or ""
    return "采购代理" in text


def _procurement_contact(signal: Signal, _result: ExtractionResult | None) -> bool:
    text = signal.evidence_text or ""
    return "联系人" in text and "采购代理" not in text


def _official_phone(signal: Signal, _result: ExtractionResult | None) -> bool:
    text = signal.evidence_text or ""
    return "采购代理" not in text and "联系人" not in text


# ════════════════════════════════════════════════════════════════
# Default engine factory
# ════════════════════════════════════════════════════════════════


def default_engine(rule_set: ScoringRuleSet | None = None) -> FlagDerivationEngine:
    """Return a fully configured FlagDerivationEngine.

    All rules are validated against the ScoringRuleSet on registration.
    A typo in a flag name raises ValueError immediately.
    """
    engine = FlagDerivationEngine(rule_set=rule_set)

    # scenario_fit
    engine.register("scenario_fit", "region_brand_or_association", _region_brand_or_association)
    engine.register("scenario_fit", "prepackaged_food", _prepackaged_food)
    engine.register("scenario_fit", "agri_product_brand", _agri_product_brand)
    engine.register("scenario_fit", "gift_box_or_packaged_product", _gift_box_or_packaged_product)
    engine.register("scenario_fit", "certification_or_gi", _certification_or_gi)
    engine.register("scenario_fit", "poor_existing_qr", _poor_existing_qr)

    # timing
    engine.register("timing", "procurement_expected_within_3_months", _procurement_expected_within_3_months)
    engine.register("timing", "newly_published_tender", _newly_published_tender)
    engine.register("timing", "newly_won_project", _newly_won_project)

    # leverage
    engine.register("leverage", "multi_org_region_brand_project", _multi_org_region_brand_project)
    engine.register("leverage", "packaging_or_printing_partner", _packaging_or_printing_partner)

    # reachability (registered in priority order)
    engine.register("reachability", "agency_phone", _agency_phone)
    engine.register("reachability", "procurement_contact", _procurement_contact)
    engine.register("reachability", "official_phone", _official_phone)

    return engine
