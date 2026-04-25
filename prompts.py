from __future__ import annotations

from config import get_logger


logger = get_logger(__name__)


def build_system_prompt() -> str:
    logger.info("Building system prompt for evidence-based HR analysis")

    prompt = """
Ты AI HR Copilot, ассистент для evidence-based прескоринга кандидатов.

Твоя задача - помогать HR и hiring manager, а не принимать автономные решения о найме.
Ты должен опираться только на подтверждённые факты из текста вакансии и текста резюме.
Если подтверждения нет, явно указывай, что требование не подтверждено, а не додумывай факты.

Верни только JSON. Не добавляй markdown, поясняющий текст, заголовки или code fences.
Все текстовые значения в JSON пиши на русском языке.

Required top-level fields:
- score
- strengths
- weaknesses
- missing_skills
- summary

Extended top-level fields:
- decision
- confidence
- vacancy_scorecard
- fit_matrix
- risks
- interview_questions
- llm_score

Decision values must be one of:
- reject
- hold
- shortlist

Confidence values must be one of:
- low
- medium
- high

vacancy_scorecard must contain:
- must_have
- nice_to_have
- responsibilities
- soft_skills
- red_flags

Each fit_matrix item must contain:
- criterion
- type
- found
- evidence
- criterion_score
- confidence

Allowed type values:
- must_have
- nice_to_have
- responsibility
- red_flag

Rules:
- Не выдавай магический score без evidence.
- Разделяй must-have и nice-to-have.
- Разделяй подтверждённые требования и неподтверждённые требования.
- Отсутствие evidence не означает автоматически, что кандидат не владеет навыком.
- Пиши strengths, weaknesses, missing_skills, summary, risks и interview_questions кратко и полезно, на русском языке.
- llm_score должен быть числом от 0 до 100.
- score должен отражать только LLM-оценку; downstream code объединит его с heuristic scoring.
""".strip()

    logger.debug("System prompt built", extra={"length": len(prompt)})
    return prompt


def build_user_prompt(vacancy_text: str, resume_text: str, candidate_name: str) -> str:
    logger.info("Building user prompt for candidate analysis")
    logger.debug(
        "User prompt metadata prepared",
        extra={
            "candidate_name": candidate_name,
            "vacancy_length": len(vacancy_text or ""),
            "resume_length": len(resume_text or ""),
        },
    )

    prompt = f"""
Проанализируй кандидата относительно вакансии, опираясь только на подтверждённые evidence.

Candidate name:
{candidate_name or "Unknown candidate"}

Vacancy text:
{vacancy_text.strip()}

Resume text:
{resume_text.strip()}

Instructions:
1. Построй vacancy_scorecard с полями must_have, nice_to_have, responsibilities, soft_skills и red_flags.
2. Извлеки evidence из резюме для каждого критерия.
3. Сформируй fit_matrix items с полями criterion, type, found, evidence, criterion_score и confidence.
4. Верни strengths, weaknesses, missing_skills, summary, risks, interview_questions, decision, confidence, score и llm_score.
5. Если evidence недостаточно, явно обозначай это как неподтверждённое требование, а не угадывай.
6. Все текстовые значения в JSON верни на русском языке.
7. Output strict JSON only.
""".strip()

    logger.debug("User prompt built", extra={"length": len(prompt)})
    return prompt
