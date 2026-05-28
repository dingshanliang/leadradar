from __future__ import annotations

from leadradar.schemas import LeadScoringInput
from leadradar.scoring import score_lead


def generate_call_opening(customer_name: str, signal_title: str, recommended_package: str) -> str:
    return (
        f"您好，我看到贵单位/贵司近期有【{signal_title}】相关公开信息。"
        f"我们做的是食品和农产品包装二维码、数字标签、溯源和区域品牌数据管理工具。"
        f"想确认一下，这块是否涉及【{recommended_package}】相关需求？"
    )


def score_demo_lead() -> dict:
    result = score_lead(
        LeadScoringInput(
            signal_type="procurement_intent",
            scenario_flags=["region_brand_or_association", "agri_product_brand"],
            timing_flags=["procurement_expected_within_3_months"],
            reachability_flags=["agency_phone"],
            leverage_flags=["multi_org_region_brand_project"],
        )
    )
    return result.model_dump()
