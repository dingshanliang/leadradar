from leadradar.schemas import LeadScoringInput
from leadradar.scoring import score_lead


def test_s_grade_procurement_intent():
    result = score_lead(
        LeadScoringInput(
            signal_type="procurement_intent",
            scenario_flags=["region_brand_or_association", "agri_product_brand", "gift_box_or_packaged_product"],
            timing_flags=["procurement_expected_within_3_months"],
            reachability_flags=["procurement_contact"],
            leverage_flags=["multi_org_region_brand_project"],
        )
    )
    assert result.grade == "S"
    assert result.total_score >= 85
    assert result.breakdown["budget_strength"] == 35


def test_b_or_above_certification_lead():
    result = score_lead(
        LeadScoringInput(
            signal_type="certification_registry",
            scenario_flags=["prepackaged_food", "certification_or_gi", "multi_sku"],
            timing_flags=["recent_exhibition_or_launch"],
            reachability_flags=["official_phone"],
            leverage_flags=[],
        )
    )
    assert result.total_score >= 30
    assert result.grade in {"B", "C", "D", "A"}


def test_d_grade_irrelevant():
    result = score_lead(LeadScoringInput(signal_type="irrelevant"))
    assert result.grade == "D"
    assert result.total_score == 0
