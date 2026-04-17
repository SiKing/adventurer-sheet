# Copilot Instructions — Adventurer Sheet

## Project Overview

D&D 5e character sheet Discord bot built with Python 3.12 and discord.py. SQLite + SQLAlchemy (async) for storage, deployed on Railway via Docker.

## Starting Instructions

When analyzing this project, always read these files first:

1. **`.github/IDEAS.md`** — All project ideas and future plans (3 phases)
2. **`.github/PLAN-PHASE1.md`** — Phase 1 (Hello World pipeline) — ✅ completed
3. **`.github/PLAN-PHASE2.md`** — Phase 2 (Character sheet CRUD) — ✅ completed
4. **`.github/ARCHITECTURE.md`** — ADR-001 through ADR-009: production-first design, DB decisions, cog structure, security, active character, git workflow, dependency review

## Completed Work

- **Phase 1:** Bot scaffold, `/hello` and `/about` commands, CI/CD pipeline (GitHub Actions → Railway), Docker deployment
- **Phase 2:** Character CRUD (`/character create|view|edit|delete|list`), SQLite + SQLAlchemy async ORM, ownership security via Discord user ID, rich embeds, active character session state, seed data for dev

## Key Architecture Rules

- **ADR-001:** Production-first — never assume files exist unless in Dockerfile
- **ADR-006:** Ownership enforcement — all queries filter by `owner_id`
- **ADR-007:** Active character — in-memory, session-scoped, not persisted
- **ADR-008:** One git op at a time; bump patch version on every feature branch
- **ADR-009:** Dependency review at plan completion

## Tech Stack

- Python 3.12, discord.py ~2.4, SQLAlchemy ~2.0 (async), aiosqlite
- pytest + pytest-asyncio + pytest-cov (80%+ coverage required)
- ruff for linting
- Docker → Railway (worker process, persistent volume at `/data`)

## Project Structure

```
src/bot/             — Bot source code
  __main__.py        — Entry point (python -m bot)
  config.py          — Env var loading
  db.py              — SQLAlchemy models and engine
  repository.py      — Data access layer
  validators.py      — Pure validation functions
  embeds.py          — Discord embed builders
  errors.py          — Custom exceptions
  cogs/character.py  — All /character commands
tests/               — pytest test suite
.github/             — Plans, architecture, CI workflows
```

