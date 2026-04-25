from __future__ import annotations

import re
from typing import Any

from config import DEFAULT_WEIGHT_VALUES, get_logger, normalize_weight_values
from models import ConfidenceValue, DecisionValue, FitMatrixItem, RequirementType, VacancyScorecard


logger = get_logger(__name__)

STOP_WORDS = {
    "and",
    "or",
    "with",
    "using",
    "the",
    "for",
    "опыт",
    "знание",
    "навык",
    "работы",
    "умение",
    "skills",
    "skill",
}
YEAR_PATTERN = re.compile(r"(\d+)\s*\+?\s*(?:years?|yrs?|год(?:а)?|лет)", re.IGNORECASE)


def normalize_weights(weight_values: dict[str, float] | None = None) -> dict[str, float]:
    logger.debug("Normalizing heuristic scoring weights", extra={"weight_values": weight_values or {}})

    weight_values = weight_values or DEFAULT_WEIGHT_VALUES
    hard_skills = float(weight_values.get("hard_skills", DEFAULT_WEIGHT_VALUES["hard_skills"]))
    experience = float(weight_values.get("experience", DEFAULT_WEIGHT_VALUES["experience"]))
    soft_skills = float(weight_values.get("soft_skills", DEFAULT_WEIGHT_VALUES["soft_skills"]))

    normalized = normalize_weight_values(hard_skills, experience, soft_skills)
    logger.debug("Heuristic scoring weights normalized", extra=normalized)
    return normalized


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _tokenize_requirement(requirement: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Zа-яА-Я0-9+#.]{2,}", _normalize_text(requirement))
    filtered_tokens = [token for token in tokens if token not in STOP_WORDS]
    return filtered_tokens


def _requirement_matches(requirement: str, resume_text: str) -> bool:
    normalized_requirement = _normalize_text(requirement)
    normalized_resume = _normalize_text(resume_text)
    if not normalized_requirement:
        return False

    if normalized_requirement in normalized_resume:
        return True

    requirement_tokens = _tokenize_requirement(requirement)
    if not requirement_tokens:
        return False

    return all(token in normalized_resume for token in requirement_tokens)


def _extract_max_years(text: str) -> int:
    matches = YEAR_PATTERN.findall(text or "")
    if not matches:
        return 0
    return max(int(match) for match in matches)


def calculate_hard_skills_score(requirements: list[str], resume_text: str) -> float:
    logger.debug(
        "Calculating hard skills score",
        extra={
            "requirements_count": len(requirements),
            "resume_text_length": len(resume_text or ""),
        },
    )

    relevant_requirements = [item for item in requirements if item.strip()]
    if not relevant_requirements:
        logger.warning("No hard skill requirements provided for scoring")
        return 0.0

    matched_count = sum(1 for requirement in relevant_requirements if _requirement_matches(requirement, resume_text))
    score = (matched_count / len(relevant_requirements)) * 100
    logger.info(
        "Hard skills score calculated",
        extra={
            "matched_count": matched_count,
            "requirements_count": len(relevant_requirements),
            "score": score,
        },
    )
    return score


def calculate_experience_score(requirements: list[str], resume_text: str) -> float:
    logger.debug(
        "Calculating experience score",
        extra={
            "requirements": requirements,
            "resume_text_length": len(resume_text or ""),
        },
    )

    required_years = _extract_max_years(" ".join(requirements))
    resume_years = _extract_max_years(resume_text)

    if required_years <= 0:
        logger.warning("No experience requirement detected for scoring")
        return 0.0

    score = min(100.0, (resume_years / required_years) * 100) if resume_years > 0 else 0.0
    logger.info(
        "Experience score calculated",
        extra={
            "required_years": required_years,
            "resume_years": resume_years,
            "score": score,
        },
    )
    return score


def calculate_soft_skills_score(requirements: list[str], resume_text: str) -> float:
    logger.debug(
        "Calculating soft skills score",
        extra={
            "requirements_count": len(requirements),
            "resume_text_length": len(resume_text or ""),
        },
    )

    relevant_requirements = [item for item in requirements if item.strip()]
    if not relevant_requirements:
        logger.warning("No soft skill requirements provided for scoring")
        return 0.0

    matched_count = sum(1 for requirement in relevant_requirements if _requirement_matches(requirement, resume_text))
    score = (matched_count / len(relevant_requirements)) * 100
    logger.info(
        "Soft skills score calculated",
        extra={
            "matched_count": matched_count,
            "requirements_count": len(relevant_requirements),
            "score": score,
        },
    )
    return score


def combine_scores(heuristic_score: float, llm_score: float) -> float:
    logger.debug(
        "Combining heuristic and LLM scores",
        extra={
            "heuristic_score": heuristic_score,
            "llm_score": llm_score,
        },
    )
    final_score = (heuristic_score * 0.45) + (llm_score * 0.55)
    clamped_score = max(0.0, min(100.0, final_score))
    logger.info("Final score combined", extra={"final_score": clamped_score})
    return clamped_score


def calculate_heuristic_score(
    scorecard: VacancyScorecard,
    resume_text: str,
    weight_values: dict[str, float] | None = None,
) -> dict[str, Any]:
    logger.info("Calculating heuristic score from scorecard and resume text")
    normalized_weights = normalize_weights(weight_values)

    hard_skill_requirements = scorecard.must_have + scorecard.nice_to_have
    experience_requirements = scorecard.must_have + scorecard.responsibilities
    soft_skill_requirements = scorecard.soft_skills

    component_scores = {
        "hard_skills": calculate_hard_skills_score(hard_skill_requirements, resume_text)
        if hard_skill_requirements
        else 0.0,
        "experience": calculate_experience_score(experience_requirements, resume_text)
        if experience_requirements
        else 0.0,
        "soft_skills": calculate_soft_skills_score(soft_skill_requirements, resume_text)
        if soft_skill_requirements
        else 0.0,
    }

    selected_weights = {
        key: normalized_weights[key]
        for key, value in component_scores.items()
        if value > 0 or {
            "hard_skills": bool(hard_skill_requirements),
            "experience": bool(experience_requirements),
            "soft_skills": bool(soft_skill_requirements),
        }[key]
    }

    if selected_weights:
        selected_total = sum(selected_weights.values())
        active_weights = {
            "hard_skills": 0.0,
            "experience": 0.0,
            "soft_skills": 0.0,
        }
        for key, value in selected_weights.items():
            active_weights[key] = value / selected_total
    else:
        active_weights = normalize_weights()

    heuristic_score = (
        component_scores["hard_skills"] * active_weights["hard_skills"]
        + component_scores["experience"] * active_weights["experience"]
        + component_scores["soft_skills"] * active_weights["soft_skills"]
    )
    logger.info(
        "Heuristic score calculated",
        extra={
            "heuristic_score": heuristic_score,
            "component_scores": component_scores,
            "active_weights": active_weights,
        },
    )

    return {
        "heuristic_score": max(0.0, min(100.0, heuristic_score)),
        "component_scores": component_scores,
        "weights": active_weights,
    }


def apply_decision_rules(
    final_score: float,
    fit_matrix: list[FitMatrixItem] | None = None,
    risks: list[str] | None = None,
    current_decision: DecisionValue | str | None = None,
) -> tuple[DecisionValue, ConfidenceValue]:
    logger.debug(
        "Applying deterministic decision rules",
        extra={
            "final_score": final_score,
            "fit_matrix_items": len(fit_matrix or []),
            "risks_count": len(risks or []),
            "current_decision": str(current_decision or ""),
        },
    )

    fit_matrix = fit_matrix or []
    risks = risks or []
    decision = DecisionValue(current_decision) if current_decision else None

    must_have_gaps = [
        item
        for item in fit_matrix
        if item.type == RequirementType.MUST_HAVE and not item.found
    ]
    red_flag_hits = [
        item
        for item in fit_matrix
        if item.type == RequirementType.RED_FLAG and item.found
    ]

    if red_flag_hits or len(must_have_gaps) >= 2:
        logger.warning(
            "Rejecting candidate due to deterministic rule",
            extra={
                "must_have_gaps": len(must_have_gaps),
                "red_flag_hits": len(red_flag_hits),
            },
        )
        return DecisionValue.REJECT, ConfidenceValue.HIGH

    if decision is None:
        if final_score >= 75:
            decision = DecisionValue.SHORTLIST
        elif final_score >= 45:
            decision = DecisionValue.HOLD
        else:
            decision = DecisionValue.REJECT

    if must_have_gaps and decision == DecisionValue.SHORTLIST:
        logger.warning(
            "Downgrading shortlist decision because must-have evidence is incomplete",
            extra={"must_have_gaps": len(must_have_gaps)},
        )
        decision = DecisionValue.HOLD

    if risks and decision == DecisionValue.SHORTLIST:
        confidence = ConfidenceValue.MEDIUM
    elif final_score >= 80 or red_flag_hits or must_have_gaps:
        confidence = ConfidenceValue.HIGH
    elif final_score >= 50:
        confidence = ConfidenceValue.MEDIUM
    else:
        confidence = ConfidenceValue.LOW

    logger.info(
        "Deterministic decision rules applied",
        extra={
            "decision": decision.value,
            "confidence": confidence.value,
            "must_have_gaps": len(must_have_gaps),
            "red_flag_hits": len(red_flag_hits),
        },
    )
    return decision, confidence
