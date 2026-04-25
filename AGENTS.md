# AGENTS.md

> Project map for AI coding agents. Keep this file aligned with the current MVP scope.

## Project Overview

AI HR Copilot is a compact Streamlit MVP for evidence-based candidate prescreening.
It is a decision-support tool for homework and portfolio use, not an ATS, CRM, or autonomous hiring system.

## Tech Stack

- Language: Python 3.11+
- UI: Streamlit
- Validation: Pydantic v2
- LLM: OpenAI SDK
- Parsing: `pdfplumber`
- Tests: `pytest`
- Storage: local JSON file
- Containerization: Docker + Docker Compose

## Current Repository State

Core MVP implementation now exists:

- `app.py` - Streamlit UI and orchestration
- `config.py` - env loading, settings, logging defaults, weight normalization helpers
- `parser.py` - PDF/manual resume parsing and cleanup
- `prompts.py` - prompt builders and JSON contract
- `gpt_service.py` - OpenAI integration and safe JSON parsing
- `scoring.py` - heuristic scoring and decision rules
- `models.py` - Pydantic v2 models and fallback normalization
- `storage.py` - local JSON history storage
- `tests/` - parser, scoring, models, storage, and app smoke tests
- `Dockerfile` / `docker-compose.yml` - containerized run path
- `.ai-factory/*` - project context, roadmap, and implementation plan

## Key Application Files

- `app.py` - Streamlit UI and orchestration
- `config.py` - env loading and settings
- `parser.py` - PDF/manual resume parsing and cleanup
- `prompts.py` - prompt builders and output contract
- `gpt_service.py` - OpenAI integration and JSON parsing
- `scoring.py` - heuristic scoring and final score composition
- `models.py` - Pydantic models and validation
- `storage.py` - local JSON history
- `tests/test_parser.py` - parser tests
- `tests/test_scoring.py` - scoring tests
- `tests/test_models.py` - model tests
- `tests/test_storage.py` - storage tests
- `tests/test_app_smoke.py` - Streamlit import smoke test

## AI Context Files

- `AGENTS.md` - project map for agents
- `.ai-factory/DESCRIPTION.md` - product scope and constraints
- `.ai-factory/ARCHITECTURE.md` - architecture and module boundaries
- `.ai-factory/ROADMAP.md` - milestones and future direction
- `.ai-factory/PLAN.md` - implementation task breakdown

## Development Rules

- Keep scope limited to compact evidence-based HR Copilot MVP.
- Do not expand product into ATS/CRM features.
- Do not implement application code when task is only planning or context setup.
- Preserve the core workflow:
  `vacancy -> scorecard -> resume parsing -> evidence extraction -> fit matrix -> heuristic_score + llm_score -> final_score -> decision -> interview questions -> history`
- Required output fields must always exist:
  - `score`
  - `strengths`
  - `weaknesses`
  - `missing_skills`
  - `summary`
- Extended fields must degrade gracefully:
  - `decision`
  - `confidence`
  - `vacancy_scorecard`
  - `fit_matrix`
  - `risks`
  - `interview_questions`
- Keep `heuristic_score`, `llm_score`, and `final_score` separate.
- App must not crash without `OPENAI_API_KEY` before analyze action.
- `.env` must not be committed.
- `data/history.json` must not be committed.
- `data/.gitkeep` may be committed.

## Verification Commands

Run these after implementation work:

- `pytest`
- `streamlit run app.py`
- `docker compose up --build`

## Agent Guidance

- Read `.ai-factory/DESCRIPTION.md` before planning features.
- Read `.ai-factory/ARCHITECTURE.md` before proposing file structure or module boundaries.
- Use `.ai-factory/ROADMAP.md` for milestone-level prioritization.
- Use `.ai-factory/PLAN.md` for implementation sequencing.
- Prefer minimal, explainable changes.
- Evidence-based HR logic is the product core; keyword-only matching is not enough.
