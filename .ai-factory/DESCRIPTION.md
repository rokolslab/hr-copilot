# AI HR Copilot

## Problem

Рекрутерам и hiring manager нужен компактный инструмент для первичного отбора кандидатов, который не сводит оценку к непрозрачному "магическому score" и не требует полноценной ATS/CRM-системы.

## Target User

- HR / recruiter, которому нужен быстрый evidence-based прескоринг
- Hiring manager, которому важно увидеть подтвержденные и неподтвержденные требования вакансии
- Reviewer домашнего задания или портфолио, который оценивает продуманность MVP

## MVP Goal

Сделать компактный Streamlit MVP для домашнего задания и портфолио: сервис принимает текст вакансии и резюме кандидата, извлекает evidence, формирует fit matrix, считает объяснимый score и показывает рекомендации для интервью.

## Core Workflow

`vacancy -> scorecard -> resume parsing -> evidence extraction -> fit matrix -> heuristic_score + llm_score -> final_score -> decision -> interview questions -> history`

## Product Principle

AI HR Copilot не заменяет HR и не принимает финальное решение о найме.
Это decision-support tool: он показывает, какие требования подтверждены фактами из резюме, какие не подтверждены, какие есть риски и какие вопросы стоит задать на интервью.

## Assignment Requirements

- Streamlit UI
- vacancy input
- candidate name input
- PDF resume upload
- PDF parsing via `pdfplumber`
- manual resume text fallback
- text cleanup
- text truncation via `MAX_RESUME_CHARS`
- OpenAI API connection via `.env`
- strictly structured JSON response
- required JSON fields always present:
  - `score`
  - `strengths`
  - `weaknesses`
  - `missing_skills`
  - `summary`
- local scoring by:
  - hard skills
  - experience
  - soft skills
- default weights:
  - hard skills: 60
  - experience: 25
  - soft skills: 15
- editable weights in UI
- JSON history storage
- multiple candidate history view
- candidate comparison
- JSON report download
- `Dockerfile`
- `docker-compose.yml`
- portfolio-grade `README.md`
- minimal `pytest` coverage

## Extended Portfolio Value

- Evidence-based workflow instead of plain keyword matching
- Separation of `heuristic_score`, `llm_score`, and `final_score`
- Structured `vacancy_scorecard` and `fit_matrix`
- Graceful fallback when LLM returns partial data
- Compact but explainable architecture suitable for demo, review, and portfolio presentation

## Functional Scope

### In Scope

- Single-user local MVP
- One vacancy and one candidate analysis at a time
- Local JSON history
- Candidate comparison based on saved analyses
- LLM-assisted extraction of scorecard, evidence, risks, and interview questions
- Deterministic heuristic scoring and explainable score composition

### Out of Scope

- ATS features: stages, pipelines, comments, collaboration, requisition management
- CRM features: talent pool, outreach, messaging, contact management
- authentication and authorization
- multi-user persistence
- database migrations and admin tools
- OCR-heavy parsing and image-based PDF recovery
- bulk processing and batch resume ingestion
- production-grade analytics and monitoring

## Tech Stack

- Language: Python 3.11+
- UI: Streamlit
- LLM integration: OpenAI SDK (current branch)
- Validation: Pydantic v2
- PDF parsing: `pdfplumber`
- Testing: `pytest`
- Containerization: Docker + Docker Compose
- Persistence: local JSON file

## Runtime Constraints

- `.env` must not be committed
- `data/history.json` must not be committed
- `data/.gitkeep` may be committed
- app must not crash without `OPENAI_API_KEY` until user clicks analyze
- Streamlit in Docker must listen on `0.0.0.0:8501`

## Output Contract

Required fields must always exist:

- `score`
- `strengths`
- `weaknesses`
- `missing_skills`
- `summary`

Extended fields should degrade gracefully:

- `decision`
- `confidence`
- `vacancy_scorecard`
- `fit_matrix`
- `risks`
- `interview_questions`

Scoring fields must be stored separately:

- `heuristic_score`
- `llm_score`
- `final_score`
