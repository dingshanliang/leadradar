"""Configuration management: validate and persist scoring rules."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator

DEFAULT_SCORING_PATH = Path(__file__).resolve().parents[3] / "data" / "scoring_rules.yml"


class GradeThresholds(BaseModel):
    S: int = Field(ge=0, le=100)
    A: int = Field(ge=0, le=100)
    B: int = Field(ge=0, le=100)
    C: int = Field(ge=0, le=100)
    D: int = 0

    @model_validator(mode="after")
    def check_descending(self) -> "GradeThresholds":
        values = [(k, getattr(self, k)) for k in ("S", "A", "B", "C", "D")]
        for i in range(len(values) - 1):
            if values[i][1] <= values[i + 1][1]:
                raise ValueError(
                    f"等级阈值必须严格递减: {values[i][0]}({values[i][1]}) "
                    f"应该大于 {values[i + 1][0]}({values[i + 1][1]})"
                )
        return self


class ScoringRulesUpdate(BaseModel):
    version: str = "0.1"
    max_scores: dict[str, int]
    grades: GradeThresholds
    budget_strength: dict[str, int]
    scenario_fit: dict[str, int]
    timing: dict[str, int]
    reachability: dict[str, int]
    leverage: dict[str, int]

    @model_validator(mode="after")
    def check_max_scores_sum(self) -> "ScoringRulesUpdate":
        total = sum(self.max_scores.values())
        if total != 100:
            raise ValueError(f"max_scores 总和必须等于 100，当前为 {total}")
        return self

    @model_validator(mode="after")
    def check_sub_scores_within_max(self) -> "ScoringRulesUpdate":
        dimensions = {
            "budget_strength": self.budget_strength,
            "scenario_fit": self.scenario_fit,
            "timing": self.timing,
            "reachability": self.reachability,
            "leverage": self.leverage,
        }
        for dim_name, sub_scores in dimensions.items():
            max_val = self.max_scores.get(dim_name)
            if max_val is None:
                raise ValueError(f"max_scores 中缺少维度: {dim_name}")
            for key, val in sub_scores.items():
                if val > max_val:
                    raise ValueError(
                        f"{dim_name}.{key} 的分值 {val} 超过了该维度满分 {max_val}"
                    )
        return self


def load_scoring_rules(path: Path | None = None) -> dict[str, Any]:
    path = path or DEFAULT_SCORING_PATH
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_scoring_rules(
    data: dict[str, Any], path: Path | None = None
) -> None:
    path = path or DEFAULT_SCORING_PATH
    tmp_path = path.with_suffix(".yml.tmp")
    bak_path = path.with_suffix(".yml.bak")

    # Write to temp file first
    with tmp_path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, indent=2)

    # Validate by re-reading
    with tmp_path.open("r", encoding="utf-8") as f:
        parsed = yaml.safe_load(f)
    if parsed is None:
        raise RuntimeError("写入的配置文件解析为空，操作已取消")

    # Backup original
    if path.exists():
        shutil.copy2(path, bak_path)

    # Atomic replace
    tmp_path.replace(path)


def update_scoring_rules(
    payload: ScoringRulesUpdate, path: Path | None = None
) -> dict[str, Any]:
    data = payload.model_dump()
    save_scoring_rules(data, path=path)
    return data
