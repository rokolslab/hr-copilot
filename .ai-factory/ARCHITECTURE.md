# Architecture: AI HR Copilot MVP

## Architecture Style

Компактный модульный монолит на Python.

Принцип: простой Streamlit entrypoint оркестрирует независимые модули для config, parsing, prompting, LLM analysis, scoring, validation и storage.

## System Boundary

Система остается evidence-based HR Copilot MVP.
Не расширять проект до ATS, CRM, multi-user backoffice или enterprise hiring platform.

## Target File Structure

- `app.py` - Streamlit entrypoint и UI orchestration
- `config.py` - загрузка env и runtime settings
- `parser.py` - PDF/manual resume parsing and cleanup
- `prompts.py` - prompt builders и JSON contract instructions
- `gpt_service.py` - OpenAI вызовы, parse, fallback
- `scoring.py` - heuristic scoring и final score composition
- `models.py` - Pydantic v2 models и output normalization
- `storage.py` - JSON history storage
- `requirements.txt` - Python dependencies
- `.env.example` - documented env variables
- `.gitignore` - ignore rules
- `Dockerfile` - container image
- `docker-compose.yml` - local container run
- `README.md` - portfolio documentation
- `data/.gitkeep` - keeps `data/` tracked
- `tests/test_parser.py` - parser tests
- `tests/test_scoring.py` - scoring tests
- `tests/test_models.py` - model validation tests
- `tests/test_storage.py` - storage tests

## Module Responsibilities

### `app.py`

- collects vacancy text, candidate name, PDF/manual resume
- allows editing scoring weights in sidebar
- triggers analysis pipeline
- renders final score, decision, confidence, strengths, weaknesses, missing skills, summary
- renders scorecard, fit matrix, risks, interview questions
- exposes JSON report download
- shows history and candidate comparison

### `config.py`

- loads `.env`
- exposes `OPENAI_MODEL`, `MAX_RESUME_CHARS`, `HISTORY_PATH`
- keeps default weights `60 / 25 / 15`
- validates or normalizes runtime settings
- must not require `OPENAI_API_KEY` during module import

### `parser.py`

- extracts text from PDF via `pdfplumber`
- cleans whitespace and noisy formatting
- truncates text to `MAX_RESUME_CHARS`
- supports manual text fallback

### `prompts.py`

- contains system prompt for evidence-based HR reasoning
- contains user prompt builder from vacancy and resume text
- enforces JSON-only response contract
- forbids unsupported claims without evidence

### `gpt_service.py`

- lazily initializes OpenAI client
- sends prompt payload to model
- parses returned JSON
- validates/normalizes output with Pydantic models
- applies graceful fallback when JSON is partial or invalid

### `scoring.py`

- computes heuristic score from:
  - hard skills
  - experience
  - soft skills
- applies default or user-defined weights
- combines `heuristic_score` and `llm_score`
- calculates `final_score`
- applies deterministic decision adjustment rules

### `models.py`

- defines all Pydantic v2 schemas
- guarantees required homework fields
- provides defaults for optional extended fields
- validates score ranges and enum-like values

### `storage.py`

- ensures `data/` exists
- loads history from JSON file
- appends new analysis records
- tolerates missing or empty history file

## Data Flow

1. User enters vacancy text, candidate name, and resume source in `app.py`.
2. `config.py` provides settings and current weight configuration.
3. `parser.py` returns cleaned resume text.
4. `prompts.py` builds structured prompt instructions.
5. `gpt_service.py` obtains LLM output and validates it through `models.py`.
6. `scoring.py` computes `heuristic_score`, merges it with `llm_score`, and derives `final_score` plus deterministic decision adjustments.
7. `models.py` produces final normalized `AnalysisResult`.
8. `storage.py` persists a `HistoryRecord` to local JSON.
9. `app.py` renders result, history, comparison, and JSON download.

## Data Models

### `VacancyScorecard`

- vacancy title or label
- must-have requirements
- nice-to-have requirements
- responsibilities
- soft skills
- red flags

### `FitMatrixItem`

- criterion
- type
- found / status
- evidence
- criterion_score
- confidence

### `AnalysisResult`

Required fields:

- `score`
- `strengths`
- `weaknesses`
- `missing_skills`
- `summary`

Extended fields:

- `decision`
- `confidence`
- `vacancy_scorecard`
- `fit_matrix`
- `risks`
- `interview_questions`
- `heuristic_score`
- `llm_score`
- `final_score`

### `HistoryRecord`

- record id
- timestamp
- candidate name
- vacancy preview
- nested `AnalysisResult`

## Scoring Rules

- Use separate scoring tracks for hard skills, experience, and soft skills.
- Default weights: hard skills `60`, experience `25`, soft skills `15`.
- Allow user-adjustable weights in UI.
- Normalize weights before calculation.
- Keep `heuristic_score`, `llm_score`, and `final_score` as separate fields.
- `final_score` should be explainable through fit matrix and score breakdown.
- LLM should support evidence extraction, not replace deterministic scoring.
- Avoid wording that implies hiring automation or final hiring authority.

## Error Handling Rules

- Missing `OPENAI_API_KEY` must not break app startup.
- Error about missing API key should appear only when user triggers analysis.
- Invalid or partial LLM JSON must not crash the app.
- Required output fields must still be returned after fallback normalization.
- PDF parsing failures should degrade to safe error message or manual text fallback.
- History file absence should initialize cleanly.

## History Storage Rules

- Storage format: local JSON file defined by `HISTORY_PATH`
- expected default path: `data/history.json`
- file should not be committed
- `data/.gitkeep` may be committed
- history is acceptable for MVP and portfolio demo only
- no multi-user concurrency guarantees required

## Docker Strategy

- Build a single app container
- install dependencies from `requirements.txt`
- run Streamlit on `0.0.0.0:8501`
- mount `./data:/app/data`
- use `.env` through `docker-compose.yml`
- expose `8501:8501`

## Testing Strategy

- `tests/test_parser.py`
  - cleanup behavior
  - truncation behavior
  - manual text fallback
- `tests/test_scoring.py`
  - weight normalization
  - experience parsing
  - final score combination
- `tests/test_models.py`
  - score range validation
  - required field guarantees
  - fallback defaults
- `tests/test_storage.py`
  - missing file handling
  - save/load roundtrip
  - malformed file strategy
- smoke check
  - `streamlit` app import or startup sanity

## Dependency Rules

- `app.py` may orchestrate all modules but should not own core business logic.
- `gpt_service.py` must use `prompts.py`, `models.py`, and `config.py` instead of embedding those concerns ad hoc.
- `storage.py` should depend on validated models, not raw free-form dicts where avoidable.
- `scoring.py` should remain deterministic and testable without network access.
- `models.py` should be the contract boundary for UI, LLM response normalization, and persistence.
