from __future__ import annotations

import json
from typing import Any

import streamlit as st

from config import DEFAULT_WEIGHT_VALUES, get_logger, get_settings
from gpt_service import analyze_candidate
from parser import prepare_resume_text
from scoring import apply_decision_rules, calculate_heuristic_score, combine_scores
from storage import append_history_record, build_history_record, load_history


logger = get_logger(__name__)
WORKFLOW_TEXT = (
    "vacancy -> scorecard -> resume parsing -> evidence extraction -> fit matrix -> "
    "heuristic_score + llm_score -> final_score -> decision -> interview questions -> history"
)


def build_download_payload(result: Any) -> str:
    logger.debug(
        "Building JSON download payload",
        extra={
            "candidate_name": result.candidate_name,
            "final_score": result.final_score,
        },
    )
    return json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)


def render_analysis_result(result: Any) -> None:
    logger.debug(
        "Rendering analysis result",
        extra={
            "candidate_name": result.candidate_name,
            "fit_matrix_items": len(result.fit_matrix),
            "risks_count": len(result.risks),
        },
    )

    st.subheader("Analysis Result")

    score_column, heuristic_column, llm_column = st.columns(3)
    score_column.metric("Final Score", f"{result.final_score:.1f}")
    heuristic_column.metric("Heuristic Score", f"{result.heuristic_score:.1f}")
    llm_column.metric("LLM Score", f"{result.llm_score:.1f}")

    decision_column, confidence_column = st.columns(2)
    decision_column.metric("Decision", result.decision.value)
    confidence_column.metric("Confidence", result.confidence.value)

    st.markdown("### Required Output")
    st.write("**Strengths**")
    st.write(result.strengths or ["No strengths extracted."])
    st.write("**Weaknesses**")
    st.write(result.weaknesses or ["No weaknesses extracted."])
    st.write("**Missing Skills**")
    st.write(result.missing_skills or ["No missing skills extracted."])
    st.write("**Summary**")
    st.write(result.summary)

    st.markdown("### Vacancy Scorecard")
    st.json(result.vacancy_scorecard.model_dump(mode="json"))

    st.markdown("### Fit Matrix")
    fit_matrix_rows = [item.model_dump(mode="json") for item in result.fit_matrix]
    if fit_matrix_rows:
        st.table(fit_matrix_rows)
    else:
        st.info("Fit matrix is empty. The LLM response likely fell back to defaults.")

    st.markdown("### Risks")
    st.write(result.risks or ["No explicit risks extracted."])

    st.markdown("### Interview Questions")
    st.write(result.interview_questions or ["No interview questions generated."])

    st.download_button(
        label="Download JSON report",
        data=build_download_payload(result),
        file_name=f"{result.candidate_name or 'candidate'}-analysis.json",
        mime="application/json",
    )


def render_history_section(history_records: list[Any]) -> None:
    logger.debug("Rendering history section", extra={"history_count": len(history_records)})
    st.subheader("History")

    if not history_records:
        st.info("No saved analyses yet.")
        return

    history_rows = [
        {
            "candidate_name": record.candidate_name,
            "created_at": record.created_at.isoformat(),
            "final_score": record.analysis.final_score,
            "decision": record.analysis.decision.value,
            "confidence": record.analysis.confidence.value,
            "vacancy_excerpt": record.vacancy_excerpt,
        }
        for record in history_records
    ]
    st.table(history_rows)

    if len(history_records) < 2:
        return

    st.markdown("### Compare Candidates")
    candidate_options = {
        f"{record.candidate_name} ({record.created_at.date()})": record
        for record in history_records
    }
    left_label = st.selectbox("Candidate A", list(candidate_options.keys()), key="compare_left")
    right_label = st.selectbox("Candidate B", list(candidate_options.keys()), key="compare_right")

    left_record = candidate_options[left_label]
    right_record = candidate_options[right_label]

    compare_left_column, compare_right_column = st.columns(2)
    compare_left_column.write(
        {
            "candidate_name": left_record.candidate_name,
            "final_score": left_record.analysis.final_score,
            "decision": left_record.analysis.decision.value,
            "summary": left_record.analysis.summary,
        }
    )
    compare_right_column.write(
        {
            "candidate_name": right_record.candidate_name,
            "final_score": right_record.analysis.final_score,
            "decision": right_record.analysis.decision.value,
            "summary": right_record.analysis.summary,
        }
    )


def run_analysis(
    candidate_name: str,
    vacancy_text: str,
    manual_resume_text: str,
    uploaded_resume: Any,
    weight_values: dict[str, float],
) -> Any | None:
    settings = get_settings()
    logger.info(
        "Run analysis requested",
        extra={
            "candidate_name": candidate_name,
            "has_uploaded_resume": uploaded_resume is not None,
            "manual_resume_length": len(manual_resume_text or ""),
            "vacancy_length": len(vacancy_text or ""),
            "weight_values": weight_values,
        },
    )

    if not candidate_name.strip() or not vacancy_text.strip():
        logger.warning("Analysis blocked due to missing candidate name or vacancy text")
        st.error("Provide both candidate name and vacancy text.")
        return None

    uploaded_bytes = uploaded_resume.getvalue() if uploaded_resume is not None else None
    resume_text = prepare_resume_text(uploaded_bytes, manual_resume_text, settings.max_resume_chars)
    if not resume_text:
        logger.warning("Analysis blocked because resume text is empty after preparation")
        st.error("Provide a PDF resume or paste resume text.")
        return None

    try:
        llm_result = analyze_candidate(vacancy_text, resume_text, candidate_name, settings)
    except ValueError as error:
        logger.warning("Analysis blocked by configuration error", extra={"error_message": str(error)})
        st.error(str(error))
        return None

    heuristic_payload = calculate_heuristic_score(
        llm_result.vacancy_scorecard,
        resume_text,
        weight_values=weight_values,
    )
    heuristic_score = heuristic_payload["heuristic_score"]
    final_score = combine_scores(heuristic_score, llm_result.llm_score)
    decision, confidence = apply_decision_rules(
        final_score,
        fit_matrix=llm_result.fit_matrix,
        risks=llm_result.risks,
        current_decision=llm_result.decision,
    )

    final_result = llm_result.model_copy(
        update={
            "candidate_name": candidate_name.strip(),
            "heuristic_score": heuristic_score,
            "final_score": final_score,
            "score": final_score,
            "decision": decision,
            "confidence": confidence,
        }
    )

    history_record = build_history_record(candidate_name.strip(), vacancy_text, final_result)
    append_history_record(settings.history_path, history_record)
    logger.info(
        "Analysis completed successfully",
        extra={
            "candidate_name": final_result.candidate_name,
            "final_score": final_result.final_score,
            "decision": final_result.decision.value,
        },
    )
    return final_result


def main() -> None:
    settings = get_settings()
    st.set_page_config(page_title="AI HR Copilot", layout="wide")
    st.title("AI HR Copilot")
    st.caption("Evidence-based candidate prescreening MVP")

    st.sidebar.header("Settings")
    st.sidebar.write(f"Model: `{settings.openai_model}`")
    hard_skills_weight = st.sidebar.slider(
        "Hard skills weight",
        min_value=0,
        max_value=100,
        value=int(DEFAULT_WEIGHT_VALUES["hard_skills"]),
    )
    experience_weight = st.sidebar.slider(
        "Experience weight",
        min_value=0,
        max_value=100,
        value=int(DEFAULT_WEIGHT_VALUES["experience"]),
    )
    soft_skills_weight = st.sidebar.slider(
        "Soft skills weight",
        min_value=0,
        max_value=100,
        value=int(DEFAULT_WEIGHT_VALUES["soft_skills"]),
    )
    st.sidebar.write(f"MAX_RESUME_CHARS: `{settings.max_resume_chars}`")
    st.sidebar.caption(WORKFLOW_TEXT)

    st.markdown("### Vacancy")
    vacancy_text = st.text_area("Vacancy text", height=220)

    st.markdown("### Candidate")
    candidate_name = st.text_input("Candidate name")
    uploaded_resume = st.file_uploader("Upload PDF resume", type=["pdf"])
    manual_resume_text = st.text_area("Manual resume text fallback", height=220)

    if "latest_result" not in st.session_state:
        st.session_state["latest_result"] = None

    if st.button("Analyze candidate", type="primary"):
        logger.debug("Analyze button clicked")
        st.session_state["latest_result"] = run_analysis(
            candidate_name=candidate_name,
            vacancy_text=vacancy_text,
            manual_resume_text=manual_resume_text,
            uploaded_resume=uploaded_resume,
            weight_values={
                "hard_skills": float(hard_skills_weight),
                "experience": float(experience_weight),
                "soft_skills": float(soft_skills_weight),
            },
        )

    latest_result = st.session_state.get("latest_result")
    if latest_result is not None:
        render_analysis_result(latest_result)

    history_records = load_history(settings.history_path)
    render_history_section(history_records)


if __name__ == "__main__":
    main()
