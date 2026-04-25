from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


DEFAULT_WEIGHT_VALUES = {
    "hard_skills": 60.0,
    "experience": 25.0,
    "soft_skills": 15.0,
}
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class Settings(BaseModel):
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-5-mini")
    max_resume_chars: int = Field(default=8000)
    history_path: str = Field(default="data/history.json")
    log_level: str = Field(default="DEBUG")
    hard_skills_weight: float = Field(default=DEFAULT_WEIGHT_VALUES["hard_skills"])
    experience_weight: float = Field(default=DEFAULT_WEIGHT_VALUES["experience"])
    soft_skills_weight: float = Field(default=DEFAULT_WEIGHT_VALUES["soft_skills"])

    @field_validator("max_resume_chars")
    @classmethod
    def validate_max_resume_chars(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("MAX_RESUME_CHARS must be greater than zero")
        return value

    @field_validator("history_path")
    @classmethod
    def validate_history_path(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("HISTORY_PATH must not be empty")
        return normalized_value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized_value = value.strip().upper()
        if normalized_value not in VALID_LOG_LEVELS:
            raise ValueError(
                f"LOG_LEVEL must be one of: {', '.join(sorted(VALID_LOG_LEVELS))}"
            )
        return normalized_value

    @field_validator(
        "hard_skills_weight",
        "experience_weight",
        "soft_skills_weight",
    )
    @classmethod
    def validate_weight(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Score weights must be non-negative")
        return float(value)

    @property
    def has_openai_api_key(self) -> bool:
        return bool(self.openai_api_key.strip())

    def safe_log_context(self) -> dict[str, Any]:
        return {
            "openai_model": self.openai_model,
            "max_resume_chars": self.max_resume_chars,
            "history_path": self.history_path,
            "log_level": self.log_level,
            "has_openai_api_key": self.has_openai_api_key,
            "weight_values": self.weight_values,
        }

    @property
    def weight_values(self) -> dict[str, float]:
        return {
            "hard_skills": self.hard_skills_weight,
            "experience": self.experience_weight,
            "soft_skills": self.soft_skills_weight,
        }


def configure_logging(log_level: str) -> None:
    logging.basicConfig(level=getattr(logging, log_level, logging.DEBUG), format=LOG_FORMAT)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def normalize_weight_values(
    hard_skills: float,
    experience: float,
    soft_skills: float,
) -> dict[str, float]:
    logger = get_logger(__name__)
    logger.debug(
        "Normalizing score weights",
        extra={
            "hard_skills": hard_skills,
            "experience": experience,
            "soft_skills": soft_skills,
        },
    )

    total = hard_skills + experience + soft_skills
    if total <= 0:
        logger.warning(
            "Received non-positive total weight, falling back to defaults",
            extra={"total": total},
        )
        hard_skills = DEFAULT_WEIGHT_VALUES["hard_skills"]
        experience = DEFAULT_WEIGHT_VALUES["experience"]
        soft_skills = DEFAULT_WEIGHT_VALUES["soft_skills"]
        total = hard_skills + experience + soft_skills

    normalized_weights = {
        "hard_skills": hard_skills / total,
        "experience": experience / total,
        "soft_skills": soft_skills / total,
    }
    logger.debug("Normalized score weights ready", extra=normalized_weights)
    return normalized_weights


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()
    raw_settings = {
        "openai_api_key": __import__("os").getenv("OPENAI_API_KEY", ""),
        "openai_model": __import__("os").getenv("OPENAI_MODEL", "gpt-5-mini"),
        "max_resume_chars": int(__import__("os").getenv("MAX_RESUME_CHARS", "8000")),
        "history_path": __import__("os").getenv("HISTORY_PATH", "data/history.json"),
        "log_level": __import__("os").getenv("LOG_LEVEL", "DEBUG"),
        "hard_skills_weight": float(
            __import__("os").getenv(
                "HARD_SKILLS_WEIGHT",
                str(DEFAULT_WEIGHT_VALUES["hard_skills"]),
            )
        ),
        "experience_weight": float(
            __import__("os").getenv(
                "EXPERIENCE_WEIGHT",
                str(DEFAULT_WEIGHT_VALUES["experience"]),
            )
        ),
        "soft_skills_weight": float(
            __import__("os").getenv(
                "SOFT_SKILLS_WEIGHT",
                str(DEFAULT_WEIGHT_VALUES["soft_skills"]),
            )
        ),
    }

    configure_logging(str(raw_settings["log_level"]).strip().upper())
    logger = get_logger(__name__)
    logger.info("Initializing application settings")

    settings = Settings(**raw_settings)
    logger.debug("Application settings loaded", extra=settings.safe_log_context())
    if not settings.has_openai_api_key:
        logger.warning(
            "OPENAI_API_KEY is not configured; analysis will fail only when invoked"
        )

    return settings
