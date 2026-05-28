from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from leadradar.schemas import ExtractionResult


class LLMProvider(ABC):
    @abstractmethod
    async def extract(self, *, text: str, url: str | None = None, title: str | None = None) -> ExtractionResult:
        """Extract a structured sales signal from public text."""


class MockLLMProvider(LLMProvider):
    async def extract(self, *, text: str, url: str | None = None, title: str | None = None) -> ExtractionResult:
        return ExtractionResult.model_validate(
            {
                "is_relevant": True,
                "signal_type": "procurement_intent",
                "customer_type": "region_brand_government",
                "organization_name": "某县农业农村局",
                "project_name": title or "某县农产品区域公用品牌建设项目",
                "budget_amount": {"value": 1800000, "currency": "CNY", "raw": "180万元"},
                "expected_time": "2026-07",
                "region": {"province": "江西省", "city": None, "county": "某县"},
                "need_summary": "区域品牌建设、产品包装、品牌推广、数字化展示",
                "matched_keywords": ["区域公用品牌", "农产品品牌"],
                "product_fit": ["区域品牌数字化管理包", "包装扫码增长包"],
                "budget_source_guess": ["区域品牌运营预算"],
                "evidence": [
                    {"field": "budget_amount", "text": "预算金额：180万元"},
                    {"field": "project_name", "text": title or "农产品区域公用品牌建设"},
                ],
                "confidence": 0.86,
                "uncertainties": [],
            }
        )


class OpenAICompatibleLLMProvider(LLMProvider):
    def __init__(self, *, api_key: str, base_url: str | None, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def extract(self, *, text: str, url: str | None = None, title: str | None = None) -> ExtractionResult:
        raise NotImplementedError(
            "Implement with an OpenAI-compatible chat/completions or responses API. "
            "Tests must use MockLLMProvider and never call external APIs."
        )


def validate_extraction(result: ExtractionResult) -> ExtractionResult:
    """Central place for additional business validation beyond Pydantic."""
    evidence_fields = {e.field for e in result.evidence}
    if result.budget_amount and result.budget_amount.value and "budget_amount" not in evidence_fields:
        result.confidence = min(result.confidence, 0.6)
        result.uncertainties.append("budget_amount lacks evidence")
    return result
