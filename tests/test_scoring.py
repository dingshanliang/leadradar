import pytest

from leadradar.schemas import LeadScoringInput
from leadradar.scoring import load_scoring_rules, score_lead
from leadradar.services.scoring_rule_set import ScoringRuleSet


@pytest.fixture
def rules():
    return load_scoring_rules()


# ── S grade (85+) ──────────────────────────────────────────────


def test_s_grade_procurement_intent(rules):
    result = score_lead(
        LeadScoringInput(
            signal_type="procurement_intent",
            scenario_flags=[
                "region_brand_or_association",
                "agri_product_brand",
                "gift_box_or_packaged_product",
            ],
            timing_flags=["procurement_expected_within_3_months"],
            reachability_flags=["procurement_contact"],
            leverage_flags=["multi_org_region_brand_project"],
        ),
        rules=rules,
    )
    assert result.grade == "S"
    assert result.total_score >= 85
    assert result.breakdown["budget_strength"] == 35


# ── A grade (70-84) ────────────────────────────────────────────


def test_a_grade_tender_notice(rules):
    result = score_lead(
        LeadScoringInput(
            signal_type="tender_notice",
            scenario_flags=["prepackaged_food", "multi_sku"],
            timing_flags=["newly_published_tender"],
            reachability_flags=["agency_phone"],
            leverage_flags=[],
        ),
        rules=rules,
    )
    assert result.total_score >= 70
    assert result.grade == "A"


# ── B grade (55-69) ────────────────────────────────────────────


def test_b_grade_winning_notice(rules):
    result = score_lead(
        LeadScoringInput(
            signal_type="winning_notice",
            scenario_flags=["agri_product_brand", "certification_or_gi"],
            timing_flags=["newly_won_project"],
            reachability_flags=["official_phone"],
            leverage_flags=[],
        ),
        rules=rules,
    )
    assert result.total_score >= 55
    assert result.grade == "B"


# ── C grade (40-54) ────────────────────────────────────────────


def test_d_grade_recruiting_low_signal(rules):
    result = score_lead(
        LeadScoringInput(
            signal_type="recruiting_signal",
            scenario_flags=["prepackaged_food"],
            timing_flags=["job_post_within_30_days"],
            reachability_flags=["official_phone"],
            leverage_flags=[],
        ),
        rules=rules,
    )
    assert result.total_score >= 30
    assert result.grade == "D"


def test_c_grade_recruiting_with_moderate_flags(rules):
    result = score_lead(
        LeadScoringInput(
            signal_type="recruiting_signal",
            scenario_flags=["region_brand_or_association"],
            timing_flags=["job_post_within_30_days"],
            reachability_flags=["official_phone"],
            leverage_flags=["leading_enterprise_replicable"],
        ),
        rules=rules,
    )
    assert result.total_score >= 40
    assert result.grade == "C"


# ── D grade (<40) ──────────────────────────────────────────────


def test_d_grade_irrelevant(rules):
    result = score_lead(LeadScoringInput(signal_type="irrelevant"), rules=rules)
    assert result.grade == "D"
    assert result.total_score == 0


def test_d_grade_news_weak_signal(rules):
    result = score_lead(
        LeadScoringInput(
            signal_type="company_website",
            scenario_flags=[],
            timing_flags=[],
            reachability_flags=["platform_customer_service"],
            leverage_flags=[],
        ),
        rules=rules,
    )
    assert result.grade == "D"
    assert result.total_score < 40


# ── Scenario fit cap at 25 ─────────────────────────────────────


def test_scenario_fit_capped_at_25(rules):
    result = score_lead(
        LeadScoringInput(
            signal_type="procurement_intent",
            scenario_flags=[
                "region_brand_or_association",
                "prepackaged_food",
                "agri_product_brand",
                "multi_sku",
                "gift_box_or_packaged_product",
                "certification_or_gi",
                "poor_existing_qr",
            ],
            timing_flags=[],
            reachability_flags=[],
            leverage_flags=[],
        ),
        rules=rules,
    )
    assert result.breakdown["scenario_fit"] <= 25


# ── Grade boundary: exact thresholds ───────────────────────────


def test_grade_for_score_exact_boundaries(rules):
    rs = ScoringRuleSet(data=rules)
    assert rs.grade_for_total(85) == "S"
    assert rs.grade_for_total(84) == "A"
    assert rs.grade_for_total(70) == "A"
    assert rs.grade_for_total(69) == "B"
    assert rs.grade_for_total(55) == "B"
    assert rs.grade_for_total(54) == "C"
    assert rs.grade_for_total(40) == "C"
    assert rs.grade_for_total(39) == "D"
    assert rs.grade_for_total(0) == "D"


# ── Empty flags ────────────────────────────────────────────────


def test_empty_flags_with_known_signal_type(rules):
    result = score_lead(
        LeadScoringInput(
            signal_type="tender_notice",
            scenario_flags=[],
            timing_flags=[],
            reachability_flags=[],
            leverage_flags=[],
        ),
        rules=rules,
    )
    assert result.total_score == 35
    assert result.grade == "D"


# ── Unknown signal type ────────────────────────────────────────


def test_unknown_signal_type_gets_zero_budget(rules):
    result = score_lead(
        LeadScoringInput(signal_type="unknown_future_type"),
        rules=rules,
    )
    assert result.breakdown["budget_strength"] == 0
    assert result.total_score == 0


# ── Reasons are populated ──────────────────────────────────────


def test_reasons_populated_for_scoring_lead(rules):
    result = score_lead(
        LeadScoringInput(
            signal_type="procurement_intent",
            scenario_flags=["region_brand_or_association"],
            timing_flags=["procurement_expected_within_3_months"],
            reachability_flags=["procurement_contact"],
            leverage_flags=["multi_org_region_brand_project"],
        ),
        rules=rules,
    )
    assert len(result.reasons) >= 4


def test_no_reasons_for_zero_score(rules):
    result = score_lead(LeadScoringInput(signal_type="irrelevant"), rules=rules)
    assert result.reasons == []


# ── Breakdown keys always present ──────────────────────────────


def test_breakdown_keys(rules):
    result = score_lead(LeadScoringInput(signal_type="news_report"), rules=rules)
    expected_keys = {"budget_strength", "scenario_fit", "timing", "reachability", "leverage"}
    assert set(result.breakdown.keys()) == expected_keys
