"""Tests for T-503: Call script generation based on customer type + signal + product package."""

from leadradar.services.call_script import generate_call_script


class TestCallScriptStructure:
    def test_returns_required_fields(self):
        script = generate_call_script(
            customer_type="region_brand_government",
            organization_name="某县农业农村局",
            signal_title="某县农产品区域公用品牌建设项目",
            signal_type="procurement_intent",
            recommended_package="区域品牌数字化管理包",
            budget_amount=1800000,
        )
        assert "opening" in script
        assert "questions" in script
        assert "wechat_follow_up" in script

    def test_opening_mentions_organization(self):
        script = generate_call_script(
            customer_type="region_brand_government",
            organization_name="某县农业农村局",
            signal_title="某县农产品区域公用品牌建设项目",
            signal_type="procurement_intent",
            recommended_package="区域品牌数字化管理包",
        )
        assert "某县农业农村局" in script["opening"]

    def test_opening_mentions_signal(self):
        script = generate_call_script(
            customer_type="region_brand_government",
            organization_name="某县农业农村局",
            signal_title="某县农产品区域公用品牌建设项目",
            signal_type="procurement_intent",
            recommended_package="区域品牌数字化管理包",
        )
        assert "农产品区域公用品牌" in script["opening"]

    def test_questions_are_relevant(self):
        script = generate_call_script(
            customer_type="region_brand_government",
            organization_name="某县农业农村局",
            signal_title="某县农产品区域公用品牌建设项目",
            signal_type="procurement_intent",
            recommended_package="区域品牌数字化管理包",
        )
        assert len(script["questions"]) >= 3


class TestCallScriptByCustomerType:
    def test_region_brand_government_has_brand_focus(self):
        script = generate_call_script(
            customer_type="region_brand_government",
            organization_name="某县农业农村局",
            signal_title="区域品牌建设项目",
            signal_type="procurement_intent",
            recommended_package="区域品牌数字化管理包",
        )
        text = script["opening"] + " ".join(script["questions"])
        assert any(k in text for k in ("区域品牌", "品牌数字化", "授权企业"))

    def test_food_enterprise_has_compliance_focus(self):
        script = generate_call_script(
            customer_type="food_enterprise",
            organization_name="某食品公司",
            signal_title="预包装食品标签升级",
            signal_type="tender_notice",
            recommended_package="数字标签合规启动包",
        )
        text = script["opening"] + " ".join(script["questions"])
        assert any(k in text for k in ("合规", "标签", "数字标签"))

    def test_unknown_customer_type_uses_generic(self):
        script = generate_call_script(
            customer_type="unknown_type",
            organization_name="某公司",
            signal_title="采购公告",
            signal_type="tender_notice",
            recommended_package="溯源信任包",
        )
        assert script["opening"]  # still generates something
        assert len(script["questions"]) >= 2


class TestCallScriptBySignalType:
    def test_procurement_intent_emphasizes_timing(self):
        script = generate_call_script(
            customer_type="region_brand_government",
            organization_name="某县农业农村局",
            signal_title="品牌建设采购意向",
            signal_type="procurement_intent",
            recommended_package="区域品牌数字化管理包",
        )
        text = script["opening"] + " ".join(script["questions"])
        assert any(k in text for k in ("预算", "采购", "意向"))

    def test_tender_notice_emphasizes_action(self):
        script = generate_call_script(
            customer_type="region_brand_government",
            organization_name="某县农业农村局",
            signal_title="品牌建设招标公告",
            signal_type="tender_notice",
            recommended_package="区域品牌数字化管理包",
        )
        text = script["opening"]
        assert any(k in text for k in ("招标", "公告"))


class TestWechatFollowUp:
    def test_wechat_follow_up_mentions_package(self):
        script = generate_call_script(
            customer_type="region_brand_government",
            organization_name="某县农业农村局",
            signal_title="品牌建设采购意向",
            signal_type="procurement_intent",
            recommended_package="区域品牌数字化管理包",
        )
        assert "区域品牌数字化管理包" in script["wechat_follow_up"]

    def test_wechat_follow_up_is_concise(self):
        script = generate_call_script(
            customer_type="region_brand_government",
            organization_name="某县农业农村局",
            signal_title="品牌建设采购意向",
            signal_type="procurement_intent",
            recommended_package="区域品牌数字化管理包",
        )
        assert len(script["wechat_follow_up"]) <= 300


class TestBudgetInScript:
    def test_budget_mentioned_when_available(self):
        script = generate_call_script(
            customer_type="region_brand_government",
            organization_name="某县农业农村局",
            signal_title="品牌建设采购意向",
            signal_type="procurement_intent",
            recommended_package="区域品牌数字化管理包",
            budget_amount=1800000,
        )
        text = script["opening"] + " ".join(script["questions"])
        assert "180" in text or "预算" in text

    def test_no_budget_still_works(self):
        script = generate_call_script(
            customer_type="region_brand_government",
            organization_name="某县农业农村局",
            signal_title="品牌建设采购意向",
            signal_type="procurement_intent",
            recommended_package="区域品牌数字化管理包",
        )
        assert script["opening"]
