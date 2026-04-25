from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from config import Settings, get_logger
from models import AnalysisResult, build_analysis_result
from prompts import build_system_prompt, build_user_prompt


logger = get_logger(__name__)


def ensure_openai_configured(settings: Settings) -> None:
    logger.debug(
        "Checking OpenAI configuration before analysis",
        extra={
            "has_openai_api_key": settings.has_openai_api_key,
            "openai_model": settings.openai_model,
        },
    )
    if not settings.has_openai_api_key:
        logger.warning("OpenAI analysis requested without API key")
        raise ValueError("OPENAI_API_KEY is not configured. Add it to .env before analysis.")


def create_openai_client(settings: Settings) -> OpenAI:
    ensure_openai_configured(settings)
    logger.info("Creating OpenAI client")
    return OpenAI(api_key=settings.openai_api_key)


def extract_response_text(response: Any) -> str:
    logger.debug("Extracting text from OpenAI response")

    output_text = getattr(response, "output_text", "")
    if output_text:
        logger.debug("Using response.output_text", extra={"length": len(output_text)})
        return output_text

    output_items = getattr(response, "output", []) or []
    collected_chunks: list[str] = []
    for item in output_items:
        content_items = getattr(item, "content", []) or []
        for content_item in content_items:
            text = getattr(content_item, "text", "")
            if text:
                collected_chunks.append(text)

    extracted_text = "\n".join(collected_chunks).strip()
    logger.debug("Collected response text from output blocks", extra={"length": len(extracted_text)})
    return extracted_text


def parse_llm_json(raw_content: str) -> dict[str, Any]:
    logger.debug("Parsing LLM JSON payload", extra={"raw_length": len(raw_content or "")})
    if not raw_content.strip():
        logger.warning("LLM returned empty response content")
        return {}

    try:
        parsed_payload = json.loads(raw_content)
        logger.debug(
            "LLM JSON parsed successfully",
            extra={"payload_keys": sorted(parsed_payload.keys()) if isinstance(parsed_payload, dict) else []},
        )
        return parsed_payload if isinstance(parsed_payload, dict) else {}
    except json.JSONDecodeError as error:
        logger.warning(
            "Failed to parse LLM JSON response",
            extra={
                "error_message": str(error),
                "raw_preview": raw_content[:300],
            },
        )
        return {}


def analyze_candidate(
    vacancy_text: str,
    resume_text: str,
    candidate_name: str,
    settings: Settings,
) -> AnalysisResult:
    logger.info(
        "Starting OpenAI candidate analysis",
        extra={
            "candidate_name": candidate_name,
            "vacancy_length": len(vacancy_text or ""),
            "resume_length": len(resume_text or ""),
            "model": settings.openai_model,
        },
    )

    client = create_openai_client(settings)
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(vacancy_text, resume_text, candidate_name)

    try:
        response = client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw_content = extract_response_text(response)
        parsed_payload = parse_llm_json(raw_content)
        analysis_result = build_analysis_result(parsed_payload, candidate_name=candidate_name)
        logger.info(
            "OpenAI candidate analysis completed",
            extra={
                "candidate_name": analysis_result.candidate_name,
                "llm_score": analysis_result.llm_score,
                "decision": analysis_result.decision.value,
            },
        )
        return analysis_result
    except Exception as error:
        logger.error(
            "OpenAI candidate analysis failed, returning fallback analysis",
            extra={
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )
        fallback_result = build_analysis_result(
            {
                "strengths": [],
                "weaknesses": ["LLM analysis failed"],
                "missing_skills": [],
                "summary": "LLM analysis could not be completed. Review the resume manually.",
                "decision": "hold",
                "confidence": "low",
                "risks": [str(error)],
                "interview_questions": [
                    "Can you walk through the most relevant achievements from your resume?"
                ],
                "llm_score": 0,
                "score": 0,
                "final_score": 0,
            },
            candidate_name=candidate_name,
        )
        return fallback_result
