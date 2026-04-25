# AI HR Copilot

AI HR Copilot is a compact Streamlit MVP for evidence-based candidate prescreening.
It is a decision-support tool for homework and portfolio use, not an ATS, CRM, or autonomous hiring system.

## Problem

Recruiters and hiring managers often need a fast first-pass candidate review, but a plain keyword matcher is too shallow and a full ATS is too heavy for a compact MVP.

## Solution

This project evaluates one candidate against one vacancy through a structured workflow that surfaces evidence, gaps, risks, and interview questions instead of hiding everything behind a black-box score.

## Evidence-Based Workflow

`vacancy -> scorecard -> resume parsing -> evidence extraction -> fit matrix -> heuristic_score + llm_score -> final_score -> decision -> interview questions -> history`

## Why This Is Not Keyword Matching

- The LLM is instructed to extract evidence, not invent fit.
- The app distinguishes must-have, nice-to-have, responsibilities, and red flags.
- Missing evidence is treated as unconfirmed, not automatically false.
- `heuristic_score`, `llm_score`, and `final_score` are stored separately.
- The final recommendation is explainable through the fit matrix and deterministic rules.

## Features

- Streamlit UI
- vacancy input
- candidate name input
- PDF resume upload via `pdfplumber`
- manual resume text fallback
- resume cleanup and truncation via `MAX_RESUME_CHARS`
- OpenAI JSON analysis
- deterministic local scoring for hard skills, experience, and soft skills
- adjustable score weights in UI
- local JSON history
- candidate comparison view
- JSON report download
- Docker support
- pytest coverage for parser, models, scoring, storage, and app import smoke

## Project Structure

```text
.
├── app.py
├── config.py
├── parser.py
├── prompts.py
├── gpt_service.py
├── scoring.py
├── models.py
├── storage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── data/
│   └── .gitkeep
└── tests/
    ├── conftest.py
    ├── test_app_smoke.py
    ├── test_models.py
    ├── test_parser.py
    ├── test_scoring.py
    └── test_storage.py
```

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## Docker Run

```bash
docker compose up --build
```

If `.env` does not exist yet:

```bash
cp .env.example .env
docker compose up --build
```

The app is exposed on `http://localhost:8501`.

## Environment Variables

Defined in `.env.example`:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `MAX_RESUME_CHARS`
- `HISTORY_PATH`
- `LOG_LEVEL`
- `HARD_SKILLS_WEIGHT`
- `EXPERIENCE_WEIGHT`
- `SOFT_SKILLS_WEIGHT`

Important runtime behavior:

- the app must not crash without `OPENAI_API_KEY` before the user clicks Analyze
- `.env` must not be committed
- `data/history.json` must not be committed

## Output JSON Schema

Required fields always present:

- `score`
- `strengths`
- `weaknesses`
- `missing_skills`
- `summary`

Extended fields with graceful fallback:

- `decision`
- `confidence`
- `vacancy_scorecard`
- `fit_matrix`
- `risks`
- `interview_questions`
- `heuristic_score`
- `llm_score`
- `final_score`

`vacancy_scorecard` contains:

- `must_have`
- `nice_to_have`
- `responsibilities`
- `soft_skills`
- `red_flags`

Each `fit_matrix` item contains:

- `criterion`
- `type`
- `found`
- `evidence`
- `criterion_score`
- `confidence`

## Verification

```bash
pytest
streamlit run app.py
docker compose up --build
```

## Limitations

- LLM may still return invalid or partial JSON; the app falls back safely but cannot guarantee perfect analysis quality.
- PDF parsing can be noisy on badly formatted resumes.
- Heuristic scoring is intentionally simple and explainable, not production-grade ranking logic.
- Local JSON history is suitable for a demo MVP, not for multi-user production use.

## Roadmap

- SQLite or PostgreSQL instead of local JSON
- DOCX support
- OCR for scanned resumes
- hh.ru integration
- PDF or Markdown export
- model comparison across multiple OpenAI models

## Homework Coverage

This MVP covers the assignment requirements through:

- Streamlit interface
- vacancy input
- candidate name input
- PDF parsing with `pdfplumber`
- manual text fallback
- `.env`-based OpenAI integration
- strict JSON response contract
- mandatory output fields
- local scoring with editable weights
- JSON history and candidate comparison
- JSON report download
- Dockerfile and `docker-compose.yml`
- portfolio-grade README
- minimal pytest suite
