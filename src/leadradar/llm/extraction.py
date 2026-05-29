from __future__ import annotations

import re
from abc import ABC, abstractmethod

from leadradar.schemas import ExtractionResult


class LLMProvider(ABC):
    @abstractmethod
    async def extract(
        self, *, text: str, url: str | None = None, title: str | None = None
    ) -> ExtractionResult:
        """Extract a structured sales signal from public text."""


class MockLLMProvider(LLMProvider):
    async def extract(
        self, *, text: str, url: str | None = None, title: str | None = None
    ) -> ExtractionResult:
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


class ExtractionResponse:
    """Wrapper that carries the ExtractionResult plus optional metadata."""

    def __init__(
        self,
        result: ExtractionResult,
        *,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        latency_ms: int | None = None,
    ):
        self.result = result
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.latency_ms = latency_ms


class OpenAICompatibleLLMProvider(LLMProvider):
    def __init__(self, *, api_key: str, base_url: str | None, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def extract(
        self, *, text: str, url: str | None = None, title: str | None = None
    ) -> ExtractionResult:
        import json
        import time

        import httpx

        base = (self.base_url or "https://api.openai.com/v1").rstrip("/")
        endpoint = f"{base}/chat/completions"

        system_prompt = (
            "你是一个 B2B 销售情报抽取助手。从政府采购/公共资源公告中抽取结构化信息。"
            "规则：1) 只抽取原文明确提及的信息，绝不编造。"
            "2) 如果缺少预算金额，budget_amount.value 设为 null。"
            "3) 所有结论必须有 evidence 字段佐证，引用原文。"
            "4) 如果文档与食品/农产品/包装/品牌/溯源无关，设 is_relevant=false。"
            "返回严格的 JSON 格式。"
        )
        user_content = f"标题：{title or '未知'}\n来源URL：{url or '未知'}\n\n正文：\n{text[:4000]}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        start = time.monotonic()
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
        elapsed_ms = int((time.monotonic() - start) * 1000)

        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        result = ExtractionResult.model_validate(parsed)

        usage = data.get("usage", {})
        result.__extraction_meta = ExtractionResponse(
            result,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            latency_ms=elapsed_ms,
        )
        return result


_CONFIDENCE_FLOOR = 0.3
_CONFIDENCE_PENALTY = 0.15
_PHONE_PATTERN = re.compile(r"1[3-9]\d{9}")
_PERSONAL_PHONE_KEYWORDS = ("手机", "个人电话", "联系电话")


def validate_extraction(result: ExtractionResult) -> ExtractionResult:
    """Validate extraction result: evidence checks, anti-fabrication, field completeness."""
    if not result.is_relevant:
        return result

    evidence_fields = {e.field for e in result.evidence}

    # ── Evidence checks ──────────────────────────────────────────
    if (
        result.budget_amount
        and result.budget_amount.value
        and "budget_amount" not in evidence_fields
    ):
        result.confidence = min(result.confidence, 0.6)
        result.uncertainties.append("budget_amount lacks evidence")

    if result.organization_name and "organization_name" not in evidence_fields:
        result.uncertainties.append("organization_name lacks evidence")

    # ── Anti-fabrication: personal phone numbers ─────────────────
    for evidence in result.evidence:
        if _PHONE_PATTERN.search(evidence.text):
            result.uncertainties.append("evidence contains suspected personal phone number")
            result.confidence -= _CONFIDENCE_PENALTY
            break

    # Check need_summary for embedded personal info
    summary = result.need_summary or ""
    if _PHONE_PATTERN.search(summary):
        result.uncertainties.append("need_summary contains suspected personal phone")

    # ── Field completeness ───────────────────────────────────────
    if not result.budget_amount or result.budget_amount.value is None:
        result.uncertainties.append("missing budget amount")

    if not result.expected_time:
        result.uncertainties.append("missing expected_time")

    # ── Confidence floor ─────────────────────────────────────────
    result.confidence = max(result.confidence, _CONFIDENCE_FLOOR)

    return result
