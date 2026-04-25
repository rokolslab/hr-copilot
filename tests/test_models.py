from pydantic import ValidationError

from models import AnalysisResult, FitMatrixItem, RequirementType, build_analysis_result


def test_analysis_result_rejects_score_above_hundred() -> None:
    try:
        AnalysisResult(
            score=101,
            strengths=[],
            weaknesses=[],
            missing_skills=[],
            summary="Summary",
            final_score=101,
        )
    except ValidationError:
        return

    raise AssertionError("AnalysisResult should reject scores above 100")


def test_build_analysis_result_applies_fallback_defaults() -> None:
    result = build_analysis_result({"llm_score": 82}, candidate_name="Jane Doe")

    assert result.candidate_name == "Jane Doe"
    assert result.score == 0
    assert result.final_score == 0
    assert result.llm_score == 82
    assert result.summary == "Insufficient evidence to generate a summary."
    assert result.decision == "hold"
    assert result.confidence == "low"
    assert result.strengths == []
    assert result.vacancy_scorecard.must_have == []
    assert result.fit_matrix == []


def test_analysis_result_validates_nested_models() -> None:
    result = build_analysis_result(
        {
            "score": 76,
            "heuristic_score": 70,
            "llm_score": 81,
            "final_score": 76,
            "strengths": ["Strong Python background"],
            "weaknesses": ["Limited leadership evidence"],
            "missing_skills": ["Airflow"],
            "summary": "Candidate matches most core backend requirements.",
            "vacancy_scorecard": {
                "must_have": ["Python", "SQL"],
                "nice_to_have": ["Airflow"],
                "responsibilities": ["Build data pipelines"],
                "soft_skills": ["Communication"],
                "red_flags": ["No production API work"],
            },
            "fit_matrix": [
                {
                    "criterion": "Python",
                    "type": RequirementType.MUST_HAVE.value,
                    "found": True,
                    "evidence": ["5 years of Python development"],
                    "criterion_score": 95,
                    "confidence": "high",
                }
            ],
        },
        candidate_name="Jane Doe",
    )

    assert result.candidate_name == "Jane Doe"
    assert result.vacancy_scorecard.must_have == ["Python", "SQL"]
    assert result.vacancy_scorecard.soft_skills == ["Communication"]
    assert len(result.fit_matrix) == 1

    item: FitMatrixItem = result.fit_matrix[0]
    assert item.type == RequirementType.MUST_HAVE
    assert item.criterion_score == 95
