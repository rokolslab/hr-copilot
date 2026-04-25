# Implementation Plan: AI HR Copilot MVP

Created: 2026-04-25
Mode: Fast

## Settings

- Testing: yes
- Logging: verbose
- Docs: yes

## Sources of Truth

- `.ai-factory/DESCRIPTION.md`
- `.ai-factory/ARCHITECTURE.md`
- `.ai-factory/ROADMAP.md`
- `AGENTS.md`
- `MVP_PLAN.md`

## Goal

Реализовать компактный Streamlit MVP для evidence-based прескоринга кандидатов без расширения scope до ATS/CRM. MVP должен поддерживать workflow:

`vacancy -> scorecard -> resume parsing -> evidence extraction -> fit matrix -> heuristic_score + llm_score -> final_score -> decision -> interview questions -> history`

## Task Checklist

- [x] Task 1 - project skeleton and repository hygiene
- [x] Task 2 - runtime configuration and settings contract
- [x] Task 3 - core data models and output contract
- [x] Task 4 - resume parsing and cleanup
- [x] Task 5 - deterministic heuristic scoring
- [x] Task 6 - prompt contract for evidence-based JSON analysis
- [x] Task 7 - OpenAI service with safe parsing and fallback
- [x] Task 8 - local JSON history storage
- [x] Task 9 - Streamlit MVP UI and end-to-end orchestration
- [x] Task 10 - containerization
- [x] Task 11 - test suite hardening and verification pass
- [x] Task 12 - portfolio README

## Scope

### In Scope

- Single-user local MVP
- Streamlit UI для анализа одного кандидата против одной вакансии
- PDF upload + manual resume text fallback
- PDF parsing через `pdfplumber`
- text cleanup и truncation через `MAX_RESUME_CHARS`
- OpenAI JSON analysis с evidence-based output
- локальный heuristic scoring по hard skills, experience, soft skills
- editable weights в UI
- раздельные `heuristic_score`, `llm_score`, `final_score`
- local JSON history
- multiple candidate history view
- candidate comparison
- JSON report download
- Docker launch
- minimal pytest suite
- portfolio-grade README

### Out of Scope

- ATS features: pipeline stages, comments, collaboration, requisitions
- CRM features: outreach, contacts, talent pools
- auth, roles, permissions
- multi-user persistence
- databases and migrations
- OCR-heavy parsing
- batch processing and bulk ingestion
- autonomous hiring decisions

## Architecture Summary

Architecture style: compact modular monolith.

Planned modules:

- `app.py` - Streamlit UI and orchestration
- `config.py` - env loading, settings, defaults, weight normalization entrypoints
- `parser.py` - PDF/manual resume extraction and cleanup
- `prompts.py` - system/user prompts and JSON contract instructions
- `gpt_service.py` - OpenAI client, request, parse, fallback normalization
- `scoring.py` - deterministic heuristic scoring and final score composition
- `models.py` - Pydantic v2 schemas and normalization contract
- `storage.py` - JSON history persistence

Core boundaries:

- UI logic stays in `app.py`
- validation contract stays in `models.py`
- deterministic score logic stays in `scoring.py`
- prompt construction stays in `prompts.py`
- OpenAI integration stays in `gpt_service.py`
- persistence stays in `storage.py`

## Implementation Phases

### Phase 1: Foundation

#### Task 1: Project skeleton and repository hygiene

- Files:
  - `requirements.txt`
  - `.gitignore`
  - `data/.gitkeep`
- Deliverable:
  - create dependency manifest
  - add ignore rules for `.env`, `data/history.json`, caches, venv
  - create `data/` placeholder
- Logging requirements:
  - none at runtime for this task
- Dependency notes:
  - first task, blocks all implementation work
- Acceptance criteria:
  - repo has installable dependency manifest
  - `.env` is ignored
  - `data/history.json` is ignored
  - `data/.gitkeep` is present

#### Task 2: Runtime configuration and settings contract

- Files:
  - `config.py`
  - `.env.example` if normalization is needed
- Deliverable:
  - load `.env`
  - expose `OPENAI_MODEL`, `MAX_RESUME_CHARS`, `HISTORY_PATH`
  - expose default scoring weights `60 / 25 / 15`
  - ensure imports do not fail without `OPENAI_API_KEY`
- Functions/classes:
  - `Settings`
  - `get_settings()`
  - helper for normalized weights if config owns this concern
- Logging requirements:
  - DEBUG: effective non-secret settings
  - INFO: settings initialization
  - WARN: missing API key as non-fatal runtime condition
- Dependency notes:
  - depends on Task 1
  - needed by parser, OpenAI service, storage, app
- Acceptance criteria:
  - module imports cleanly without `.env`
  - API key is optional until analysis action
  - weights and limits have predictable defaults
- Tests:
  - optional small config tests only if logic becomes non-trivial

#### Task 3: Core data models and output contract

- Files:
  - `models.py`
  - `tests/test_models.py`
- Deliverable:
  - add Pydantic v2 models for:
    - `VacancyScorecard`
    - `FitMatrixItem`
    - `AnalysisResult`
    - `HistoryRecord`
    - helper models/enums if needed
  - guarantee required homework fields always exist
  - provide graceful defaults for optional extended fields
- Functions/classes:
  - enums for decision/confidence/type/status values
  - normalization or fallback helper for partial LLM payload
- Logging requirements:
  - DEBUG: optional field defaults applied
  - WARN: invalid or partial payload normalized through fallback
- Dependency notes:
  - depends on Task 2
  - blocks scoring, OpenAI service, storage, UI
- Acceptance criteria:
  - score-like fields validated in `0..100`
  - required fields `score`, `strengths`, `weaknesses`, `missing_skills`, `summary` always exist after normalization
  - `heuristic_score`, `llm_score`, `final_score` represented separately
- Tests:
  - reject invalid score range
  - verify fallback defaults
  - verify nested model validation

### Phase 2: Local Processing Layer

#### Task 4: Resume parsing and cleanup

- Files:
  - `parser.py`
  - `tests/test_parser.py`
- Deliverable:
  - parse PDF via `pdfplumber`
  - clean whitespace and noisy formatting
  - truncate text to `MAX_RESUME_CHARS`
  - support manual text fallback
- Functions/classes:
  - `extract_text_from_pdf(...)`
  - `clean_text(...)`
  - `prepare_resume_text(...)`
- Logging requirements:
  - DEBUG: source type and text lengths before/after cleanup
  - INFO: parsing completed
  - WARN: PDF parse empty or fallback path used
  - ERROR: PDF parsing failed unexpectedly
- Dependency notes:
  - depends on Task 2
  - independent from OpenAI and UI
- Acceptance criteria:
  - valid manual text path works without PDF
  - output is cleaned and length-limited
  - invalid/empty PDF does not crash the analysis pipeline
- Tests:
  - cleanup removes extra spaces/newlines
  - truncation obeys limit
  - manual fallback is used correctly

#### Task 5: Deterministic heuristic scoring

- Files:
  - `scoring.py`
  - `tests/test_scoring.py`
- Deliverable:
  - implement scoring for hard skills, experience, soft skills
  - normalize weights
  - compute `heuristic_score`
  - combine with `llm_score` into `final_score`
  - apply deterministic decision adjustments for must-have gaps and red flags
- Functions/classes:
  - `normalize_weights(...)`
  - `calculate_hard_skills_score(...)`
  - `calculate_experience_score(...)`
  - `calculate_soft_skills_score(...)`
  - `calculate_heuristic_score(...)`
  - `combine_scores(...)`
  - `apply_decision_rules(...)`
- Logging requirements:
  - DEBUG: matched signals and per-component score breakdown
  - INFO: score calculation completed
  - WARN: low-evidence input reduced scoring confidence
- Dependency notes:
  - depends on Tasks 2 and 3
  - should stay network-independent and testable in isolation
- Acceptance criteria:
  - default weights `60 / 25 / 15` work
  - final score follows documented composition
  - decision rules remain explainable
- Tests:
  - experience recognition for `3 года`, `5 лет`, `2+ years`, `6 yrs`
  - weight normalization
  - score combination formula
  - must-have or red flag rule affects decision as expected

### Phase 3: LLM Analysis Layer

#### Task 6: Prompt contract for evidence-based JSON analysis

- Files:
  - `prompts.py`
- Deliverable:
  - build system prompt
  - build user prompt from vacancy and resume
  - require JSON-only response
  - instruct model to produce evidence, scorecard, fit matrix, risks, and interview questions
  - explicitly avoid unsupported claims and keyword-only reasoning
- Functions/classes:
  - `build_system_prompt()`
  - `build_user_prompt(...)`
- Logging requirements:
  - DEBUG: prompt metadata only, not full sensitive contents
  - INFO: prompt prepared for analysis
- Dependency notes:
  - depends on Tasks 2 and 3
  - blocks OpenAI service implementation
- Acceptance criteria:
  - prompt requires mandatory fields
  - prompt distinguishes must-have, nice-to-have, responsibilities, red flags, evidence, unconfirmed requirements

#### Task 7: OpenAI service with safe parsing and fallback

- Files:
  - `gpt_service.py`
  - `models.py` if fallback helpers need small extension
- Deliverable:
  - lazily initialize OpenAI client
  - fail only when analyze action is requested without API key
  - call model and parse JSON safely
  - validate and normalize payload into `AnalysisResult`
  - preserve `llm_score` separately
- Functions/classes:
  - `analyze_candidate(...)`
  - `ensure_openai_configured(...)`
  - `parse_llm_json(...)`
- Logging requirements:
  - DEBUG: request metadata, parse path, fallback reasons
  - INFO: LLM analysis started/completed
  - WARN: missing API key on action or invalid JSON received
  - ERROR: API request failure or unrecoverable parse issue
- Dependency notes:
  - depends on Tasks 2, 3, and 6
  - output must remain valid even on partial failure
- Acceptance criteria:
  - startup/import does not require API key
  - invalid JSON does not crash the app
  - output always remains compatible with required contract
- Tests:
  - mocked service tests are optional if lightweight
  - minimum contract coverage comes from model normalization tests

### Phase 4: Persistence and UI

#### Task 8: Local JSON history storage

- Files:
  - `storage.py`
  - `tests/test_storage.py`
- Deliverable:
  - create data directory if missing
  - initialize history file safely
  - load history records
  - append validated records
  - handle missing, empty, or malformed history gracefully
- Functions/classes:
  - `ensure_history_file(...)`
  - `load_history(...)`
  - `append_history_record(...)`
- Logging requirements:
  - DEBUG: path usage and record counts
  - INFO: history loaded/saved
  - WARN: malformed history reset or recovery path
  - ERROR: read/write failure
- Dependency notes:
  - depends on Tasks 2 and 3
  - should be finished before UI wiring
- Acceptance criteria:
  - missing file does not crash load
  - append works on first run
  - persisted payload remains JSON-serializable and valid
- Tests:
  - missing file handling
  - append/load roundtrip
  - malformed file recovery behavior

#### Task 9: Streamlit MVP UI and end-to-end orchestration

- Files:
  - `app.py`
  - `tests/test_app_smoke.py`
- Deliverable:
  - build sidebar for model, weights, max chars, workflow note
  - build main form for vacancy, candidate name, PDF upload, manual text
  - wire parser, prompts, OpenAI service, scoring, models, storage
  - render required fields and extended fields safely
  - show scorecard, fit matrix, risks, interview questions
  - provide JSON download
  - show history and candidate comparison
- Functions/classes:
  - keep helper functions minimal, only when they reduce rendering duplication
- Logging requirements:
  - DEBUG: analyze action, chosen resume input path, state transitions
  - INFO: analysis completed and history persisted
  - WARN: missing form inputs or missing API key on action
- Dependency notes:
  - depends on Tasks 2 through 8
  - should remain thin orchestration layer
- Acceptance criteria:
  - `streamlit run app.py` starts
  - app does not crash without API key until analyze is clicked
  - required output fields are always visible
  - comparison view works on stored history
  - JSON report download works
- Tests:
  - import smoke test for `app.py`

### Phase 5: Packaging, Verification, Documentation

#### Task 10: Containerization

- Files:
  - `Dockerfile`
  - `docker-compose.yml`
- Deliverable:
  - build app image from Python 3.11+
  - install `requirements.txt`
  - run Streamlit on `0.0.0.0:8501`
  - mount `./data:/app/data`
  - use `.env` via compose `env_file`
  - expose `8501:8501`
- Logging requirements:
  - app logs should stay visible in container stdout/stderr
- Dependency notes:
  - depends on runnable local app from Task 9
- Acceptance criteria:
  - `docker compose up --build` starts the app
  - history persists via mounted volume
  - container respects env configuration

#### Task 11: Test suite hardening and verification pass

- Files:
  - `tests/test_parser.py`
  - `tests/test_scoring.py`
  - `tests/test_models.py`
  - `tests/test_storage.py`
  - `tests/test_app_smoke.py`
- Deliverable:
  - finalize minimal but stable pytest suite
  - close any coverage gaps around parser, scoring, models, storage, app smoke
- Logging requirements:
  - no new runtime logging required; tests should validate deterministic behavior
- Dependency notes:
  - depends on implementation of relevant modules
  - may be updated incrementally during earlier tasks, but this is the explicit hardening pass
- Acceptance criteria:
  - `pytest` passes
  - critical contracts and fragile logic are covered

#### Task 12: Portfolio README

- Files:
  - `README.md`
- Deliverable:
  - rewrite README as portfolio-grade landing page
  - explain problem, solution, evidence-based workflow, why it is not keyword matching, local run, Docker run, env, JSON schema, limitations, roadmap, and homework coverage
- Logging requirements:
  - none
- Dependency notes:
  - last task after implementation behavior is stable
- Acceptance criteria:
  - README matches actual implementation
  - product framing remains decision-support, not hiring automation

## Implementation Order

Recommended execution order for `/aif-implement`:

1. Task 1 - project skeleton and repository hygiene
2. Task 2 - runtime configuration and settings contract
3. Task 3 - core data models and output contract
4. Task 4 - resume parsing and cleanup
5. Task 5 - deterministic heuristic scoring
6. Task 6 - prompt contract for evidence-based JSON analysis
7. Task 7 - OpenAI service with safe parsing and fallback
8. Task 8 - local JSON history storage
9. Task 9 - Streamlit MVP UI and end-to-end orchestration
10. Task 10 - containerization
11. Task 11 - test suite hardening and verification pass
12. Task 12 - portfolio README

Why this order:

- it establishes config and contract first
- it implements deterministic core pieces before network-dependent logic
- it keeps storage separate from UI concerns
- it ensures the app is locally runnable before Docker and README finalization

## Risks and Constraints

- Invalid JSON from LLM
  - Mitigation: strict JSON prompt, safe parsing, Pydantic normalization, fallback defaults
- Noisy PDF parsing
  - Mitigation: cleanup, truncation, manual text fallback
- Missing API key
  - Mitigation: lazy client init and analyze-time validation only
- Weak heuristic scoring
  - Mitigation: conservative deterministic rules and visible score separation
- History JSON is not production-grade
  - Mitigation: keep it explicitly MVP-only and single-user
- False certainty from missing evidence
  - Mitigation: distinguish confirmed, partial, missing, and unconfirmed states
- Scope creep into ATS/CRM
  - Mitigation: follow `DESCRIPTION.md`, `ARCHITECTURE.md`, and `AGENTS.md` boundaries strictly

## Verification Checklist

- `pytest`
- `streamlit run app.py`
- `docker compose up --build`
- `.env.example` present and accurate
- `.gitignore` excludes `.env` and `data/history.json`
- `data/.gitkeep` committed
- required fields always present
- extended fields degrade gracefully
- `heuristic_score`, `llm_score`, `final_score` stored separately
- history save/load works
- JSON download works
- README aligned with actual behavior

## Commit Plan

Checkpoint 1 after Tasks 1-3:

- `chore: scaffold MVP foundations and data contracts`

Checkpoint 2 after Tasks 4-6:

- `feat: add parsing scoring and prompt contracts`

Checkpoint 3 after Tasks 7-9:

- `feat: implement analysis pipeline history and Streamlit UI`

Checkpoint 4 after Tasks 10-12:

- `chore: add docker verification tests and portfolio docs`

## Ready for /aif-implement

Ready for /aif-implement: yes

Continue with command:

```text
/aif-implement
```
