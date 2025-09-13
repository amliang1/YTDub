# Repository Guidelines

## Project Structure & Module Organization
- `app/`: FastAPI app. Core config (`core/`), DB and Celery, routes (`routes/`), business logic (`services/`), models (`models/`), background tasks (`workers/`).
- `tests/`: Unit/integration tests named `test_*.py`.
- `alembic/`, `alembic.ini`: Database migrations.
- Runtime artifacts: `downloads/`, `processed_videos/`, `temp/`, `test_outputs/`, optional `storage/` (managed by `StorageService`).
- Docker: `Dockerfile`, `docker-compose.yml`.

## Build, Test, and Development Commands
- Setup env:
  - `python -m venv venv && source venv/bin/activate`
  - `pip install -r requirements.txt`
- Run API locally: `uvicorn app.main:app --reload` (serves FastAPI on `:8000`).
- Containers (API, Postgres, Redis, Celery, Flower): `docker-compose up --build` (Flower UI at `:5555`).
- Tests:
  - Fast run: `pytest -q`
  - With coverage: `pytest --cov=app --cov-report=term-missing`
  - Alt runner: `python run_tests.py`

## Coding Style & Naming Conventions
- Python 3.9+, 4‑space indent, follow PEP 8; add type hints and docstrings.
- Names: `snake_case` for files/functions, `PascalCase` for classes, `UPPER_SNAKE` for constants.
- Module layout:
  - Place domain logic in `app/services/` (e.g., `video_downloader.py`, `translator.py`).
  - HTTP endpoints in `app/routes/<resource>.py` (use FastAPI `Depends` for DB via `app.core.database.get_db`).
  - Background work in `app/workers/` (Celery tasks included by `app.core.celery_app`).

## Testing Guidelines
- Put tests under `tests/` and name `test_*.py`. Prefer small, deterministic unit tests.
- Use pytest; unittest-style tests are fine. Mock external calls (network, `yt-dlp`, `ffmpeg`, TTS) and filesystem effects.
- Use `test_outputs/` or `tmp_path` for temp files; clean up after tests.

## Commit & Pull Request Guidelines
- Commits: imperative, scoped when helpful. Example: `feat(services): add StorageService.save_tts_audio` or `fix(routes): handle 404 for videos`.
- PRs must include:
  - Summary, rationale, and linked issue.
  - How to test (commands, sample request).
  - Screenshots/logs for behavior changes.
  - Checklist: tests pass, new tests added/updated, docs touched, no secrets committed, migrations added if models changed.

## Security & Config Tips
- Use `.env` for `POSTGRES_*`, `REDIS_*`, and any API keys; never commit secrets.
- Ensure Redis and Postgres are running for Celery flows; install `ffmpeg` locally when running outside Docker.
