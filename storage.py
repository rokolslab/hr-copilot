from __future__ import annotations

import json
from pathlib import Path

from config import get_logger
from models import AnalysisResult, HistoryRecord


logger = get_logger(__name__)


def ensure_history_file(path: str) -> Path:
    history_path = Path(path)
    logger.debug("Ensuring history file exists", extra={"path": str(history_path)})

    history_path.parent.mkdir(parents=True, exist_ok=True)
    if not history_path.exists():
        history_path.write_text("[]", encoding="utf-8")
        logger.info("History file created", extra={"path": str(history_path)})

    return history_path


def load_history(path: str) -> list[HistoryRecord]:
    history_path = ensure_history_file(path)
    logger.info("Loading history records", extra={"path": str(history_path)})

    raw_content = history_path.read_text(encoding="utf-8").strip()
    if not raw_content:
        logger.warning("History file is empty; reinitializing with empty list")
        history_path.write_text("[]", encoding="utf-8")
        return []

    try:
        raw_records = json.loads(raw_content)
        if not isinstance(raw_records, list):
            raise ValueError("History JSON must contain a list")
    except (json.JSONDecodeError, ValueError) as error:
        logger.warning(
            "History file is malformed; resetting to empty list",
            extra={
                "path": str(history_path),
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )
        history_path.write_text("[]", encoding="utf-8")
        return []

    history_records = [HistoryRecord.model_validate(item) for item in raw_records]
    logger.info("History records loaded", extra={"count": len(history_records)})
    return history_records


def append_history_record(path: str, record: HistoryRecord) -> None:
    history_path = ensure_history_file(path)
    existing_records = load_history(path)
    logger.info(
        "Appending history record",
        extra={
            "path": str(history_path),
            "existing_count": len(existing_records),
            "candidate_name": record.candidate_name,
        },
    )

    existing_records.append(record)
    serialized_records = [item.model_dump(mode="json") for item in existing_records]
    history_path.write_text(
        json.dumps(serialized_records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("History record appended", extra={"new_count": len(existing_records)})


def build_history_record(candidate_name: str, vacancy_text: str, analysis: AnalysisResult) -> HistoryRecord:
    logger.debug(
        "Building history record",
        extra={
            "candidate_name": candidate_name,
            "vacancy_length": len(vacancy_text or ""),
            "final_score": analysis.final_score,
        },
    )
    return HistoryRecord(
        candidate_name=candidate_name,
        vacancy_excerpt=(vacancy_text or "").strip()[:200],
        analysis=analysis,
    )
