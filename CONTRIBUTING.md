# Contributing to Ariya

Thanks for thinking about contributing! This document explains how to set up a dev environment, the coding conventions, and the PR workflow.

## Ground rules

1. **Open an issue first** for anything larger than a small bug fix or doc tweak — it saves everyone time.
2. Be kind in reviews and discussions. We assume good intent.
3. Never commit real secrets. `.env` files are git-ignored; use `.env.example` as a template.

## Development setup

See the [Quick start](README.md#quick-start) section of the README for a step-by-step guide to running the backend and frontend locally.

Briefly:

```bash
# Backend
cd backend && python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

## Coding conventions

### Python (backend)

- Python **3.11+**, type-hinted everywhere.
- Pydantic v2 models for every request/response shape — no untyped dicts in the API surface.
- Keep side effects out of `services/` functions; they should be pure where possible and take explicit inputs.
- Format with `black`, lint with `ruff` (optional but encouraged).

### TypeScript (frontend)

- `strict: true` in `tsconfig.json`. No `any` unless there's a documented reason.
- Functional React components with hooks. No class components.
- Co-locate component styles in `styles.css` using the design tokens defined at the top.
- Keep the `lib/api.ts` surface narrow — one typed wrapper per backend endpoint.

### Commits

Follow [Conventional Commits](https://www.conventionalcommits.org) where practical:

```
feat: add multi-file JOIN analysis
fix(sandbox): handle timeout errors in auto-repair loop
docs: clarify OPENAI_MODEL env var options
refactor(api): extract artifact normalization into its own module
```

## Pull request checklist

Before you open a PR:

- [ ] The app still runs locally end-to-end (upload CSV → ask question → see chart).
- [ ] No real API keys or user data in the diff.
- [ ] New env vars are documented in both `.env.example` files and the README.
- [ ] New endpoints have updated Pydantic schemas **and** TypeScript types in `frontend/src/lib/api.ts`.
- [ ] Screenshots or a short clip for UI changes.

## Reporting bugs

Please include:

1. What you did (steps or a CSV that reproduces it).
2. What you expected.
3. What actually happened (stack trace, screenshot, network tab).
4. Your OS, Python version, and Node version.

## Questions

Open a [discussion](../../discussions) or reach out on the profile linked in the README.
