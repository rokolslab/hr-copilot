from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from config import get_logger


logger = get_logger(__name__)


class DecisionValue(str, Enum):
    REJECT = "reject"
    HOLD = "hold"
    SHORTLIST = "shortlist"


class ConfidenceValue(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RequirementType(str, Enum):
    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"
    RESPONSIBILITY = "responsibility"
    RED_FLAG = "red_flag"


def _clamp_score(value: Any, fallback: float = 0.0) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return fallback
    return max(0.0, min(100.0, numeric_value))


def _ensure_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        normalized_items = []
        for item in value:
            text = str(item).strip()
            if text:
                normalized_items.append(text)
        return normalized_items

    text = str(value).strip()
    return [text] if text else []


class VacancyScorecard(BaseModel):
    must_have: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)

    @field_validator(
        "must_have",
        "nice_to_have",
        "responsibilities",
        "soft_skills",
        "red_flags",
        mode="before",
    )
    @classmethod
    def normalize_list_fields(cls, value: Any) -> list[str]:
        return _ensure_string_list(value)


class FitMatrixItem(BaseModel):
    criterion: str
    type: RequirementType
    found: bool = False
    evidence: list[str] = Field(default_factory=list)
    criterion_score: float = 0.0
    confidence: ConfidenceValue = ConfidenceValue.LOW

    @field_validator("criterion")
    @classmethod
    def validate_criterion(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("criterion must not be empty")
        return normalized_value

    @field_validator("evidence", mode="before")
    @classmethod
    def normalize_evidence(cls, value: Any) -> list[str]:
        return _ensure_string_list(value)

    @field_validator("criterion_score")
    @classmethod
    def validate_criterion_score(cls, value: float) -> float:
        if not 0 <= value <= 100:
            raise ValueError("criterion_score must be between 0 and 100")
        return float(value)


class AnalysisResult(BaseModel):
    score: float
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    summary: str
    candidate_name: str = ""
    decision: DecisionValue = DecisionValue.HOLD
    confidence: ConfidenceValue = ConfidenceValue.LOW
    vacancy_scorecard: VacancyScorecard = Field(default_factory=VacancyScorecard)
    fit_matrix: list[FitMatrixItem] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)
    heuristic_score: float = 0.0
    llm_score: float = 0.0
    final_score: float = 0.0

    @field_validator(
        "score",
        "heuristic_score",
        "llm_score",
        "final_score",
    )
    @classmethod
    def validate_score_fields(cls, value: float) -> float:
        if not 0 <= value <= 100:
            raise ValueError("score fields must be between 0 and 100")
        return float(value)

    @field_validator(
        "strengths",
        "weaknesses",
        "missing_skills",
        "risks",
        "interview_questions",
        mode="before",
    )
    @classmethod
    def normalize_text_lists(cls, value: Any) -> list[str]:
        return _ensure_string_list(value)

    @field_validator("summary", mode="before")
    @classmethod
    def normalize_summary(cls, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("summary must not be empty")
        return text

    @field_validator("candidate_name", mode="before")
    @classmethod
    def normalize_candidate_name(cls, value: Any) -> str:
        return str(value or "").strip()

    @model_validator(mode="after")
    def sync_score_and_final_score(self) -> AnalysisResult:
        if self.final_score == 0.0 and self.score != 0.0:
            self.final_score = self.score
        if self.score != self.final_score:
            self.score = self.final_score
        return self


class HistoryRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    candidate_name: str
    vacancy_excerpt: str
    analysis: AnalysisResult

    @field_validator("candidate_name", "vacancy_excerpt")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("text fields must not be empty")
        return normalized_value


def build_analysis_result(payload: dict[str, Any] | None, candidate_name: str = "") -> AnalysisResult:
    logger.debug(
        "Building analysis result from payload",
        extra={
            "candidate_name": candidate_name,
            "has_payload": bool(payload),
            "payload_keys": sorted(payload.keys()) if payload else [],
        },
    )

    payload = payload or {}
    required_defaults_applied: list[str] = []

    normalized_payload: dict[str, Any] = {
        "candidate_name": str(payload.get("candidate_name") or candidate_name).strip(),
        "strengths": _ensure_string_list(payload.get("strengths")),
        "weaknesses": _ensure_string_list(payload.get("weaknesses")),
        "missing_skills": _ensure_string_list(payload.get("missing_skills")),
        "summary": str(payload.get("summary") or "Insufficient evidence to generate a summary.").strip(),
        "decision": payload.get("decision") or DecisionValue.HOLD.value,
        "confidence": payload.get("confidence") or ConfidenceValue.LOW.value,
        "vacancy_scorecard": payload.get("vacancy_scorecard") or {},
        "fit_matrix": payload.get("fit_matrix") or [],
        "risks": _ensure_string_list(payload.get("risks")),
        "interview_questions": _ensure_string_list(payload.get("interview_questions")),
        "heuristic_score": _clamp_score(payload.get("heuristic_score"), fallback=0.0),
        "llm_score": _clamp_score(payload.get("llm_score"), fallback=0.0),
    }

    if "summary" not in payload or not str(payload.get("summary") or "").strip():
        required_defaults_applied.append("summary")
    for list_field_name in ("strengths", "weaknesses", "missing_skills"):
        if list_field_name not in payload:
            required_defaults_applied.append(list_field_name)

    raw_final_score = payload.get("final_score", payload.get("score"))
    raw_score = payload.get("score", raw_final_score)
    normalized_final_score = _clamp_score(raw_final_score, fallback=_clamp_score(raw_score, 0.0))
    normalized_payload["final_score"] = normalized_final_score
    normalized_payload["score"] = normalized_final_score

    if "vacancy_scorecard" not in payload:
        required_defaults_applied.append("vacancy_scorecard")
    if "fit_matrix" not in payload:
        required_defaults_applied.append("fit_matrix")
    if "decision" not in payload:
        required_defaults_applied.append("decision")
    if "confidence" not in payload:
        required_defaults_applied.append("confidence")
    if "risks" not in payload:
        required_defaults_applied.append("risks")
    if "interview_questions" not in payload:
        required_defaults_applied.append("interview_questions")

    if required_defaults_applied:
        logger.warning(
            "Analysis payload required fallback normalization",
            extra={"defaults_applied": sorted(set(required_defaults_applied))},
        )
    else:
        logger.debug("Analysis payload contained all expected keys")

    result = AnalysisResult.model_validate(normalized_payload)
    logger.debug(
        "Analysis result built successfully",
        extra={
            "candidate_name": result.candidate_name,
            "final_score": result.final_score,
            "fit_matrix_items": len(result.fit_matrix),
        },
    )
    return result
