from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from leadradar.api.auth_routes import router as auth_router
from leadradar.api.routes import router
from leadradar.config import get_settings
from leadradar.db import get_session
from leadradar.services.lead_service import generate_call_opening, score_demo_lead

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(auth_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/demo-score")
def demo_score() -> dict:
    return score_demo_lead()


@app.post("/api/v1/demo-call-script")
def demo_call_script(payload: dict) -> dict[str, object]:
    opening = generate_call_opening(
        customer_name=payload.get("customer_name", "目标客户"),
        signal_title=payload.get("signal_title", "农产品区域品牌建设项目"),
        recommended_package=payload.get("recommended_package", "区域品牌数字化管理包"),
    )
    return {
        "opening": opening,
        "questions": [
            "这个项目里是否涉及产品二维码、溯源展示或授权企业管理？",
            "当前产品标签、检测报告和溯源信息由谁维护？",
            "如果做数字化入口，一般走品牌预算、合规预算还是项目预算？",
        ],
    }
