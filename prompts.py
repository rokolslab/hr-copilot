from __future__ import annotations

from config import get_logger


logger = get_logger(__name__)


def build_system_prompt() -> str:
    logger.info("Building system prompt for evidence-based HR analysis")

    prompt = """
You are AI HR Copilot, an evidence-based candidate prescreening assistant.

Your role is to support HR and hiring managers, not to make autonomous hiring decisions.
You must reason from evidence found in the vacancy text and resume text.
If evidence is missing, say it is unconfirmed instead of inventing facts.

Return JSON only. Do not add markdown, prose, headings, or code fences.

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
- Do not produce a magical score without evidence.
- Distinguish must-have from nice-to-have.
- Distinguish confirmed evidence from missing or unconfirmed requirements.
- Missing evidence does not automatically mean the candidate lacks the skill.
- Keep strengths, weaknesses, missing_skills, risks, and interview_questions concise and useful.
- llm_score must be a number from 0 to 100.
- score must reflect the LLM assessment only; downstream code will combine it with heuristic scoring.
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
Analyze the candidate against the vacancy using evidence only.

Candidate name:
{candidate_name or "Unknown candidate"}

Vacancy text:
{vacancy_text.strip()}

Resume text:
{resume_text.strip()}

Instructions:
1. Build a vacancy scorecard with must-have, nice-to-have, responsibilities, soft_skills, and red flags.
2. Extract evidence from the resume for each criterion.
3. Build fit_matrix items with criterion, type, found, evidence, criterion_score, and confidence.
4. Return strengths, weaknesses, missing_skills, summary, risks, interview_questions, decision, confidence, score, and llm_score.
5. If evidence is incomplete, mark it as unconfirmed through the fit matrix content instead of guessing.
6. Output strict JSON only.
""".strip()

    logger.debug("User prompt built", extra={"length": len(prompt)})
    return prompt
