from models import FitMatrixItem, RequirementType, VacancyScorecard
from scoring import (
    apply_decision_rules,
    calculate_experience_score,
    calculate_heuristic_score,
    combine_scores,
    normalize_weights,
)


def test_calculate_experience_score_recognizes_russian_years() -> None:
    score = calculate_experience_score(["Требуется 3 года опыта"], "Есть 5 лет опыта в backend")

    assert score == 100


def test_calculate_experience_score_recognizes_english_years() -> None:
    score = calculate_experience_score(["Need 5 years of experience"], "Worked for 2+ years in data engineering")

    assert score == 40


def test_calculate_experience_score_recognizes_short_year_notation() -> None:
    score = calculate_experience_score(["Minimum 6 yrs with Python"], "6 yrs building backend systems")

    assert score == 100


def test_normalize_weights_returns_fractional_distribution() -> None:
    normalized = normalize_weights({"hard_skills": 60, "experience": 25, "soft_skills": 15})

    assert normalized == {
        "hard_skills": 0.6,
        "experience": 0.25,
        "soft_skills": 0.15,
    }


def test_combine_scores_uses_documented_formula() -> None:
    result = combine_scores(80, 60)

    assert result == 69


def test_apply_decision_rules_rejects_when_red_flag_is_found() -> None:
    decision, confidence = apply_decision_rules(
        82,
        fit_matrix=[
            FitMatrixItem(
                criterion="Frequent unexplained job hopping",
                type=RequirementType.RED_FLAG,
                found=True,
                evidence=["Three short tenures in one year"],
                criterion_score=0,
            )
        ],
    )

    assert decision == "reject"
    assert confidence == "high"


def test_calculate_heuristic_score_uses_dedicated_soft_skills_channel() -> None:
    scorecard = VacancyScorecard(
        must_have=["Python"],
        nice_to_have=[],
        responsibilities=["Build APIs"],
        soft_skills=["communication"],
        red_flags=[],
    )

    result = calculate_heuristic_score(
        scorecard,
        "Python developer with strong communication skills",
    )

    assert result["component_scores"]["soft_skills"] == 100
