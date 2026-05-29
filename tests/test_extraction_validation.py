"""Tests for T-303: Extraction validation — JSON, evidence, anti-fabrication."""


from leadradar.schemas import BudgetAmount, Evidence, ExtractionResult
from leadradar.llm.extraction import validate_extraction


def _base_result(**overrides) -> ExtractionResult:
    defaults = {
        "is_relevant": True,
        "signal_type": "procurement_intent",
        "customer_type": "region_brand_government",
        "organization_name": "某县农业农村局",
        "project_name": "农产品区域公用品牌建设项目",
        "budget_amount": BudgetAmount(value=1800000, raw="180万元"),
        "evidence": [
            Evidence(field="budget_amount", text="预算金额：180万元"),
            Evidence(field="organization_name", text="采购单位：某县农业农村局"),
        ],
        "confidence": 0.9,
    }
    defaults.update(overrides)
    return ExtractionResult(**defaults)


# ── Evidence checks ──────────────────────────────────────────────


class TestEvidenceChecks:
    def test_budget_without_evidence_reduces_confidence(self):
        result = _base_result(
            budget_amount=BudgetAmount(value=500000, raw="50万元"),
            evidence=[Evidence(field="organization_name", text="某县农业农村局")],
        )
        validated = validate_extraction(result)
        assert validated.confidence < 0.9
        assert any("budget_amount" in u for u in validated.uncertainties)

    def test_budget_with_evidence_keeps_confidence(self):
        result = _base_result()
        validated = validate_extraction(result)
        assert validated.confidence == 0.9

    def test_organization_name_without_evidence_adds_uncertainty(self):
        result = _base_result(
            organization_name="某县农业农村局",
            evidence=[Evidence(field="budget_amount", text="预算金额：180万元")],
        )
        validated = validate_extraction(result)
        assert any("organization_name" in u for u in validated.uncertainties)

    def test_no_key_fields_no_penalty(self):
        """If budget_amount is None and org_name has evidence, no penalties."""
        result = _base_result(
            budget_amount=None,
            evidence=[Evidence(field="organization_name", text="某县农业农村局")],
        )
        validated = validate_extraction(result)
        assert validated.confidence == 0.9


# ── Anti-fabrication checks ──────────────────────────────────────


class TestAntiFabrication:
    def test_phone_number_in_evidence_rejected(self):
        result = _base_result(
            evidence=[
                Evidence(field="contact", text="联系电话：13800138000"),
                Evidence(field="budget_amount", text="预算金额：180万元"),
            ],
        )
        validated = validate_extraction(result)
        assert any("phone" in u.lower() or "个人" in u for u in validated.uncertainties)

    def test_mobile_number_in_evidence_rejected(self):
        result = _base_result(
            evidence=[
                Evidence(field="contact", text="手机：13912345678"),
                Evidence(field="budget_amount", text="预算金额：180万元"),
            ],
        )
        validated = validate_extraction(result)
        assert any("phone" in u.lower() or "手机" in u for u in validated.uncertainties)

    def test_normal_evidence_passes(self):
        result = _base_result()
        validated = validate_extraction(result)
        assert not any("phone" in u.lower() or "手机" in u for u in validated.uncertainties)

    def test_need_summary_with_personal_info_flagged(self):
        result = _base_result(
            need_summary="张三（手机13900001111）负责此项目",
        )
        validated = validate_extraction(result)
        assert any("phone" in u.lower() for u in validated.uncertainties)


# ── Confidence floor ─────────────────────────────────────────────


class TestConfidenceFloor:
    def test_confidence_never_goes_below_floor(self):
        result = _base_result(
            confidence=0.95,
            budget_amount=BudgetAmount(value=500000),
            evidence=[Evidence(field="other", text="无预算证据")],
        )
        validated = validate_extraction(result)
        assert validated.confidence >= 0.3

    def test_irrelevant_result_not_modified(self):
        result = _base_result(is_relevant=False, signal_type="irrelevant", confidence=0.2)
        validated = validate_extraction(result)
        assert validated.confidence == 0.2


# ── Field completeness ───────────────────────────────────────────


class TestFieldCompleteness:
    def test_missing_budget_adds_uncertainty(self):
        result = _base_result(budget_amount=None)
        validated = validate_extraction(result)
        assert any("预算" in u or "budget" in u for u in validated.uncertainties)

    def test_missing_expected_time_adds_uncertainty(self):
        result = _base_result(expected_time=None)
        validated = validate_extraction(result)
        assert any("时间" in u or "time" in u for u in validated.uncertainties)

    def test_complete_result_no_uncertainties(self):
        result = _base_result(expected_time="2026-07")
        validated = validate_extraction(result)
        assert len(validated.uncertainties) == 0
