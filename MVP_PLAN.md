**Текущее состояние проекта**

В текущем репозитории почти нет реализации:

- есть `README.md` с очень краткой формулировкой идеи;
- есть `.env.example` с:
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL=gpt-5-mini`
  - `MAX_RESUME_CHARS=8000`
  - `HISTORY_PATH=data/history.json`
- нет Python-кода;
- нет `requirements.txt`;
- нет `app.py`, модулей, тестов, Docker-файлов;
- нет папки `data/`;
- нет готового учебного шаблона, который пришлось бы адаптировать.

Вывод: проект фактически на нулевой стадии, поэтому можно собрать MVP аккуратно и без лишней реорганизации.

**Слабые места текущего состояния**

1. Нет end-to-end workflow.
2. Не определены модели данных для scorecard, fit matrix, history.
3. Нет слоя валидации JSON-ответа LLM.
4. Нет локального heuristic scoring.
5. Нет UI, хранения истории, сравнения кандидатов.
6. Нет тестов, Docker и портфельного README.

**Целевой MVP Workflow**

1. HR вставляет текст вакансии.
2. HR вводит имя кандидата.
3. HR загружает PDF или вставляет текст резюме.
4. `parser.py` извлекает и очищает текст, обрезает по `MAX_RESUME_CHARS`.
5. `gpt_service.py` строит:
   - `vacancy_scorecard`
   - evidence по резюме
   - `fit_matrix`
   - `llm_score`
   - `strengths / weaknesses / missing_skills / summary`
   - `decision / confidence / risks / interview_questions`
6. `models.py` валидирует ответ через Pydantic.
7. Если расширенные поля неполные, приложение мягко подставляет дефолты и сохраняет обязательные поля ДЗ.
8. `scoring.py` считает локальный `heuristic_score` по:
   - hard skills
   - experience
   - soft skills
9. Итоговый score считается как:
   - `final_score = heuristic_score * 0.45 + llm_score * 0.55`
   - затем clamp в `0..100`
10. `decision` корректируется правилами и red flags по must-have.
11. `storage.py` сохраняет результат в `data/history.json`.
12. Streamlit показывает:
   - итог
   - scorecard
   - fit matrix
   - history
   - сравнение кандидатов
   - download JSON report

**Минимальная структура проекта**

- `app.py`
- `config.py`
- `parser.py`
- `prompts.py`
- `gpt_service.py`
- `scoring.py`
- `models.py`
- `storage.py`
- `requirements.txt`
- `.env.example`
- `.gitignore`
- `Dockerfile`
- `docker-compose.yml`
- `README.md`
- `data/history.json`
- `tests/test_parser.py`
- `tests/test_scoring.py`
- `tests/test_models.py`

Это соответствует задаче и не добавляет лишней архитектуры.

**План изменений по файлам**

`README.md`
- Переписать как портфельное описание.
- Добавить проблему, подход evidence-based, workflow, структуру, env, запуск, Docker, JSON schema, ограничения, roadmap, покрытие требований ДЗ.

`.env.example`
- Оставить текущие переменные.
- Проверить, что значения совпадают с MVP-контрактом.

`requirements.txt`
- Зафиксировать совместимые зависимости:
  - `streamlit`
  - `pdfplumber`
  - `python-dotenv`
  - `openai`
  - `pydantic`
  - `pytest`

`config.py`
- Загрузка `.env`.
- Чтение `OPENAI_MODEL`, `MAX_RESUME_CHARS`, `HISTORY_PATH`.
- Значения по умолчанию.
- Нормализация весов по категориям.

`parser.py`
- Извлечение текста из PDF через `pdfplumber`.
- Очистка лишних пробелов, пустых строк, мусорных символов.
- Ограничение длины по `MAX_RESUME_CHARS`.
- Fallback для ручного текста.

`prompts.py`
- Системный и пользовательский промпт.
- Жесткое требование JSON-ответа.
- Явный запрет на “магический score без evidence”.
- Инструкция различать:
  - must-have
  - nice-to-have
  - responsibilities
  - red flags
  - evidence
  - unconfirmed requirements

`models.py`
- Pydantic-схемы для:
  - `VacancyScorecard`
  - `FitMatrixItem`
  - `AnalysisResult`
  - `HistoryRecord`
- Валидация:
  - `score` в диапазоне `0..100`
  - enum-like поля для `decision`, `confidence`, `type`
- Дефолты для необязательных расширенных полей.

`gpt_service.py`
- Вызов OpenAI API через `.env`.
- Получение строго структурированного JSON.
- Защита от невалидного ответа:
  - parse
  - fallback
  - дефолтные поля
- Отдельно хранить `llm_score`.

`scoring.py`
- `normalize_weights`
- hard skills matching:
  - технические токены
  - стоп-слова RU/EN
  - фильтр коротких и слишком общих слов
  - словарь common tech skills
- experience scoring:
  - распознавание `3 года`, `5 лет`, `2+ years`, `6 yrs`
- soft skills scoring по RU/EN спискам
- итоговый `heuristic_score`
- финальный score и decision rules

`storage.py`
- Создание папки `data/`, если ее нет.
- Сохранение и загрузка истории из JSON.
- Добавление записи без падения на пустом/отсутствующем файле.

`app.py`
- Streamlit UI.
- Sidebar:
  - модель
  - веса
  - `MAX_RESUME_CHARS`
  - workflow
- Main:
  - `AI HR Copilot`
  - vacancy text
  - candidate name
  - PDF upload
  - manual resume text
  - button
- Result:
  - `final_score`
  - `decision`
  - `confidence`
  - обязательные поля ДЗ
  - scorecard
  - fit matrix dataframe
  - risks
  - interview questions
  - JSON download
- History:
  - таблица кандидатов
  - выбор двух кандидатов
  - compare view

`.gitignore`
- Добавить:
  - `.env`
  - `__pycache__/`
  - `.pytest_cache/`
  - `.venv/`
  - `data/history.json` или решить, хранить ли пустой файл в репо

`Dockerfile`
- Python image
- install requirements
- expose `8501`
- запуск streamlit на `0.0.0.0:8501`

`docker-compose.yml`
- сервис app
- проброс `8501:8501`
- env file
- volume при необходимости

`tests/test_parser.py`
- `clean_text` убирает лишние пробелы
- `clean_text` соблюдает лимит длины

`tests/test_scoring.py`
- `calculate_experience_score` распознает:
  - `3 года`
  - `5 лет`
  - `2+ years`
- `normalize_weights` работает корректно

`tests/test_models.py`
- Pydantic не принимает `score > 100`

Дополнительно нужен тест на storage. Логичнее добавить:
- `tests/test_storage.py`

Потому что пользовательский список тестов включает storage, а в предложенной структуре его файла нет. Это минимальная и полезная корректировка структуры.

**Минимальная реорганизация**

Так как репозиторий пустой, реорганизация не нужна.  
Единственная правка структуры, которую я бы предложил заранее:

- добавить `tests/test_storage.py`

Это лучше, чем запихивать storage-тесты в чужой файл.

**Риски реализации**

1. OpenAI может вернуть частично невалидный JSON.
2. PDF extraction может давать шумный текст.
3. Hard skills matching легко сделать слишком наивным.
4. Decision downgrade по red flags требует аккуратного правила, чтобы не ломать объяснимость.
5. История в JSON подходит для MVP, но не для многопользовательского режима.
6. Нужно особенно ясно показать в UI и тексте отчета:
   - “не найдено подтверждение” не равно “кандидат не умеет”.

**Команды запуска**

Локально:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Docker:

```bash
docker compose up --build
```

**Команды проверки**

Тесты:

```bash
pytest
```

Опционально быстрый smoke check:

```bash
streamlit run app.py
```

Docker smoke check:

```bash
docker compose up --build
```

**Критерии готовности к сдаче ДЗ**

1. Приложение запускается локально и через Docker.
2. `.env` действительно используется для OpenAI API и конфигурации.
3. PDF-резюме парсится через `pdfplumber`.
4. Очистка текста и `MAX_RESUME_CHARS` работают.
5. LLM-ответ приводится к строго структурированному JSON.
6. Обязательные поля ДЗ всегда присутствуют:
   - `score`
   - `strengths`
   - `weaknesses`
   - `missing_skills`
   - `summary`
7. Есть scoring по:
   - hard skills
   - experience
   - soft skills
8. Веса по умолчанию:
   - 60 / 25 / 15
9. Веса меняются в sidebar.
10. История сохраняется в JSON.
11. Несколько кандидатов видны в таблице.
12. Есть сравнение двух кандидатов.
13. Есть download JSON report.
14. Есть README уровня портфолио, а не учебной заглушки.
15. Есть Dockerfile и `docker-compose.yml`.
16. Базовые pytest-тесты проходят.
17. UI и текст отчета явно объясняют evidence-based подход.
18. Если расширенные поля LLM отсутствуют, приложение не падает.

**Итог**

Текущее состояние: почти пустой репозиторий, мешающих артефактов нет.  
Лучший путь: собрать компактный, объяснимый MVP вокруг `app.py + parser + gpt_service + scoring + models + storage`, не превращая проект в сложную систему раньше времени.

Если хочешь, следующим сообщением могу сделать уже **детальный implementation plan по шагам разработки** на 1-2 итерации без написания кода.
