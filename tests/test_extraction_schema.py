import pytest

from leadradar.schemas import ExtractionResult


def test_extraction_result_requires_evidence():
    with pytest.raises(Exception):
        ExtractionResult.model_validate(
            {
                "is_relevant": True,
                "signal_type": "procurement_intent",
                "confidence": 0.8,
                "evidence": [],
            }
        )


def test_extraction_result_valid():
    result = ExtractionResult.model_validate(
        {
            "is_relevant": True,
            "signal_type": "procurement_intent",
            "organization_name": "某县农业农村局",
            "budget_amount": {"value": 1800000, "currency": "CNY", "raw": "180万元"},
            "product_fit": ["区域品牌数字化管理包"],
            "evidence": [{"field": "budget_amount", "text": "预算金额180万元"}],
            "confidence": 0.86,
        }
    )
    assert result.budget_amount.value == 1800000
