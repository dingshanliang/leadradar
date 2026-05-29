from __future__ import annotations


def generate_call_script(
    *,
    customer_type: str | None = None,
    organization_name: str | None = None,
    signal_title: str | None = None,
    signal_type: str | None = None,
    recommended_package: str | None = None,
    budget_amount: float | None = None,
) -> dict[str, object]:
    opening = _build_opening(
        customer_type=customer_type,
        organization_name=organization_name or "贵单位",
        signal_title=signal_title,
        signal_type=signal_type,
        budget_amount=budget_amount,
    )
    questions = _build_questions(customer_type, recommended_package)
    wechat = _build_wechat_follow_up(
        organization_name=organization_name,
        signal_title=signal_title,
        recommended_package=recommended_package,
    )
    return {
        "opening": opening,
        "questions": questions,
        "wechat_follow_up": wechat,
    }


def _build_opening(
    *,
    customer_type: str | None,
    organization_name: str,
    signal_title: str | None,
    signal_type: str | None,
    budget_amount: float | None,
) -> str:
    signal_ref = f"【{signal_title}】" if signal_title else "相关公开信息"

    if signal_type == "procurement_intent":
        budget_hint = f"，预算金额约{_fmt_budget(budget_amount)}" if budget_amount else ""
        return (
            f"您好，我是做食品和农产品数字包装的。"
            f"我看到{organization_name}近期有{signal_ref}的采购意向{budget_hint}。"
            f"想确认一下，这个项目是否涉及二维码、溯源或品牌数字化展示方面的需求？"
        )

    if signal_type == "tender_notice":
        return (
            f"您好，我注意到{organization_name}发布了{signal_ref}的招标公告。"
            f"我们专注于食品农产品包装的数字化方案，"
            f"想了解一下是否有技术方案合作的可能？"
        )

    if signal_type == "winning_notice":
        return (
            f"您好，恭喜{organization_name}在{signal_ref}项目中顺利中标。"
            f"我们做食品农产品包装数字化工具，想看看是否有数字化落地方面的合作机会？"
        )

    return (
        f"您好，我看到{organization_name}近期有{signal_ref}相关动态。"
        f"我们专注于食品和农产品数字包装方案，想了解一下是否有相关需求？"
    )


def _build_questions(customer_type: str | None, package: str | None) -> list[str]:
    base = [
        "这个项目里是否涉及产品二维码、溯源展示或授权企业管理？",
        "当前产品标签、检测报告和溯源信息由谁维护？",
    ]

    if customer_type in ("region_brand_government", "region_brand_association"):
        base.extend(
            [
                "区域品牌下面有多少家授权企业？目前用什么方式管理授权和追溯？",
                "如果做数字化入口，一般走品牌预算、合规预算还是项目预算？",
            ]
        )
    elif customer_type == "food_enterprise":
        base.extend(
            [
                "目前产品的标签审核和营养成分标注是手动操作还是已有系统支持？",
                "出口和内销产品对标签的要求差异，你们怎么管理？",
            ]
        )
    else:
        base.append("如果做数字化入口，一般走品牌预算、合规预算还是项目预算？")

    if package and "溯源" in package:
        base.append("目前有没有溯源系统？是自建还是第三方？")

    return base


def _build_wechat_follow_up(
    *,
    organization_name: str | None,
    signal_title: str | None,
    recommended_package: str | None,
) -> str:
    org = organization_name or "贵单位"
    package = f"【{recommended_package}】" if recommended_package else "我们的数字化方案"

    return (
        f"{org}好，我是刚才电话联系的。我们做食品和农产品包装数字化工具，"
        f"针对{signal_title or '您近期的项目'}，推荐{package}。"
        f"方便发一份资料给您参考吗？"
    )


def _fmt_budget(amount: float) -> str:
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.0f}万元"
    if amount >= 10_000:
        return f"{amount / 10_000:.0f}万元"
    return f"{amount:.0f}元"
