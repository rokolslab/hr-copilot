from pathlib import Path

from models import build_analysis_result
from storage import append_history_record, build_history_record, load_history


def test_load_history_handles_missing_file(tmp_path: Path) -> None:
    history_path = tmp_path / "history.json"

    result = load_history(str(history_path))

    assert result == []
    assert history_path.exists()


def test_append_history_record_roundtrip(tmp_path: Path) -> None:
    history_path = tmp_path / "history.json"
    analysis = build_analysis_result(
        {
            "score": 72,
            "final_score": 72,
            "heuristic_score": 68,
            "llm_score": 75,
            "strengths": ["Python"],
            "weaknesses": ["Limited cloud exposure"],
            "missing_skills": ["Airflow"],
            "summary": "Strong backend profile.",
        },
        candidate_name="Jane Doe",
    )
    record = build_history_record("Jane Doe", "Backend Python Engineer", analysis)

    append_history_record(str(history_path), record)
    loaded_records = load_history(str(history_path))

    assert len(loaded_records) == 1
    assert loaded_records[0].candidate_name == "Jane Doe"
    assert loaded_records[0].analysis.final_score == 72


def test_load_history_resets_malformed_file(tmp_path: Path) -> None:
    history_path = tmp_path / "history.json"
    history_path.write_text("{not-json", encoding="utf-8")

    loaded_records = load_history(str(history_path))

    assert loaded_records == []
    assert history_path.read_text(encoding="utf-8") == "[]"
