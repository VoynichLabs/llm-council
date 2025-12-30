# Repository Guidelines

## Project Structure & Module Organization
- `backend/` (FastAPI API): endpoints in `backend/main.py`; council orchestration in `backend/council.py`; OpenRouter client in `backend/openrouter.py`; config in `backend/config.py`; JSON storage in `backend/storage.py` writing to `data/conversations/` (gitignored).
- `frontend/` (React + Vite): app in `frontend/src/` with API client `frontend/src/api.js` and components in `frontend/src/components/`.
- Root: `start.sh` (convenience runner), `pyproject.toml` (Python deps via uv), `.env` (secrets), `README.md` (setup/run).

## Build, Test, and Development Commands
- Backend setup: `uv sync`
- Backend run (localhost:8001): `uv run python -m backend.main`
- Frontend install: `cd frontend && npm install`
- Frontend dev (localhost:5173): `npm run dev`
- Lint frontend: `npm run lint`
- Build frontend: `npm run build`
- One-shot (Unix shells): `./start.sh`

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indent, type hints where practical. Use `snake_case` for modules/functions, `PascalCase` for classes. Keep FastAPI routes lightweight; put pure logic in `backend/*.py` helpers.
- JavaScript/React: Functional components, `PascalCase` component names, `camelCase` vars/functions. Keep UI state in components; API calls in `frontend/src/api.js`. Respect ESLint rules in `frontend/eslint.config.js` (fix issues before PR).

## Testing Guidelines
- No automated tests are configured yet. If adding tests:
  - Python: place in `tests/`, name `test_*.py` (pytest style). Focus on council parsing/aggregation and storage.
  - Frontend: place in `frontend/src/__tests__/`, name `*.test.jsx` (Vitest/Jest style). Test API client and rendering of stages.
  - Prefer small, fast unit tests before UI/E2E.

## Commit & Pull Request Guidelines
- Commits: imperative mood + scope prefix, e.g., `backend: add SSE streaming events` or `frontend: render stage rankings`.
- PRs: include description, run/verify steps, and screenshots/GIFs for UI. Link related issues. Update docs if config or behavior changes. Ensure `npm run lint` passes; do not commit `.env` or `data/`.

## Security & Configuration Tips
- Put `OPENROUTER_API_KEY` in root `.env` only; never in code. Adjust models/timeouts in `backend/config.py`. Handle API failures gracefully and avoid logging secrets.

## Architecture Overview
- 3-stage pipeline in `backend/council.py`; REST + SSE endpoints in `backend/main.py`. Frontend consumes the API via `frontend/src/api.js` and renders Stage 1–3 results.

