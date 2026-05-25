# Copilot Instructions — Adventurer Sheet

## Project Overview

D&D 5e character sheet Discord bot built with Python 3.12 and discord.py. PostgreSQL + SQLAlchemy (async) for storage, deployed on Railway via Docker.

## Starting Instructions

When analyzing this project, always read these files first:

1. **`.github/IDEAS.md`** — All project ideas and future plans (3 phases)
2. **`.github/PLAN-PHASE1.md`** — Phase 1 (Hello World pipeline) — ✅ completed
3. **`.github/PLAN-PHASE2.md`** — Phase 2 (Character sheet CRUD) — ✅ completed
4. **`.github/PLAN-PHASE3.md`** — Phase 3 (Additional features) — 🔲 in progress
5. **`.github/ARCHITECTURE.md`** — ADR-001 through ADR-010: production-first design, DB decisions, cog structure, security, active character, git workflow, dependency review, backup storage

## Completed Work

- **Phase 1:** Bot scaffold, `/hello` and `/about` commands, CI/CD pipeline (GitHub Actions → Railway), Docker deployment
- **Phase 2:** Character CRUD (`/character create|view|edit|delete|list`), SQLite + SQLAlchemy async ORM, ownership security via Discord user ID, rich embeds, active character session state, seed data for dev

## Phase 3 Task Backlog

| Issue | Title | Status |
|-------|-------|--------|
| [#10](https://github.com/SiKing/adventurer-sheet/issues/10) | Persistent storage (SQLite → PostgreSQL) | ✅ Complete |
| [#11](https://github.com/SiKing/adventurer-sheet/issues/11) | Backup storage | ✅ Complete |
| [#12](https://github.com/SiKing/adventurer-sheet/issues/12) | Modify stats (incremental edits) | 🔲 Not started |
| [#13](https://github.com/SiKing/adventurer-sheet/issues/13) | Post character to chat | 🔲 Not started |
| [#14](https://github.com/SiKing/adventurer-sheet/issues/14) | Combat Scores | 🔲 Not started |

## Key Architecture Rules

- **ADR-001:** Production-first — never assume files exist unless in Dockerfile
- **ADR-006:** Ownership enforcement — all queries filter by `owner_id`
- **ADR-007:** Active character — in-memory, session-scoped, not persisted
- **ADR-008:** One git op at a time; bump patch version on every feature branch
- **ADR-009:** Dependency review at plan completion

## Tech Stack

- Python 3.12, discord.py ~2.4, SQLAlchemy ~2.0 (async), asyncpg ~0.30, aiohttp ~3.13
- pytest + pytest-asyncio + pytest-cov (80%+ coverage required)
- ruff for linting
- Docker → Railway (worker process)
- Local dev: Docker Compose for PostgreSQL

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
  backup/            — Backup storage (Protocol + GitHub Releases adapter)
scripts/             — CLI utilities (backup.py, restore.py)
tests/               — pytest test suite
.github/             — Plans, architecture, CI workflows
```
