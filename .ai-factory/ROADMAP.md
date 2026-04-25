# Roadmap: AI HR Copilot

## [x] Milestone 1: Project Skeleton

- add `requirements.txt`
- add `.gitignore`
- add `data/.gitkeep`
- add base runtime modules:
  - `app.py`
  - `config.py`
  - `parser.py`
  - `prompts.py`
  - `gpt_service.py`
  - `scoring.py`
  - `models.py`
  - `storage.py`
- keep app scope constrained to MVP

## [x] Milestone 2: Parser + Models + Scoring

- parse PDF via `pdfplumber`
- support manual resume text fallback
- clean and truncate resume text
- define Pydantic v2 models
- implement heuristic scoring for hard skills, experience, and soft skills
- keep `heuristic_score`, `llm_score`, and `final_score` separate

## [x] Milestone 3: OpenAI JSON Analysis

- add strict JSON prompt contract
- generate `vacancy_scorecard`
- generate `fit_matrix`
- generate strengths, weaknesses, missing skills, summary
- generate decision, confidence, risks, interview questions
- add graceful fallback for partial or invalid JSON

## [x] Milestone 4: Streamlit UI

- build vacancy and resume input flow
- add candidate name input
- add sidebar settings and weight controls
- render result blocks for mandatory and extended fields
- ensure app does not crash without API key before analyze action

## [x] Milestone 5: History + Comparison + Report

- persist analyses in local JSON history
- show multiple candidates
- compare two candidates
- provide downloadable JSON report

## [x] Milestone 6: Docker + Tests + README

- add `Dockerfile`
- add `docker-compose.yml`
- add minimal `pytest` suite
- rewrite `README.md` for portfolio presentation
- verify local and Docker startup

## Future

- SQLite or PostgreSQL instead of local JSON
- DOCX support
- OCR for scanned resumes
- hh.ru integration
- PDF or Markdown export
- model comparison across multiple OpenAI models

## Guardrails

- do not expand roadmap into ATS/CRM scope
- prioritize explainability over feature count
- keep the MVP demo-friendly, testable, and portfolio-ready
