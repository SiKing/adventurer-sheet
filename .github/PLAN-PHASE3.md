# Phase 3 Plan — Additional Features

> **Goal:** Evolve the bot from a prototype into a production-quality application
> with persistent PostgreSQL storage, backup capability, improved UX for stat
> editing, public character posting, and combat score defaults.

---

## Overview

Phase 3 is a collection of independent feature tasks. Each task follows ADR-008:
own feature branch, patch version bump, full test coverage, documentation update.
Tasks are ordered by dependency — #10 must complete before #11.

**GitHub Issues:** All tasks are tracked as issues in the
[adventurer-sheet](https://github.com/SiKing/adventurer-sheet/issues) repository.

---

## Task Summary

| Issue | Title | Branch | Depends On | Status |
|-------|-------|--------|------------|--------|
| [#10](https://github.com/SiKing/adventurer-sheet/issues/10) | Persistent storage (SQLite → PostgreSQL) | `feat/persistent-storage` | — | ✅ Complete |
| [#11](https://github.com/SiKing/adventurer-sheet/issues/11) | Backup storage | `feat/backup-storage` | #10 | 🔄 In progress |
| [#12](https://github.com/SiKing/adventurer-sheet/issues/12) | Modify stats (incremental edits) | `feat/modify-stats` | — | ✅ Complete |
| [#13](https://github.com/SiKing/adventurer-sheet/issues/13) | Post character to chat | `feat/post-character` | — | ✅ Complete |
| [#14](https://github.com/SiKing/adventurer-sheet/issues/14) | Combat Scores | `feat/combat-scores` | — | 🔲 Not started |

---

## Task #10 — Persistent Storage (SQLite → PostgreSQL)

**Issue:** [#10](https://github.com/SiKing/adventurer-sheet/issues/10)
**Branch:** `feat/persistent-storage`
**Version bump:** `0.2.0` → `0.2.1`

### Summary

Replace SQLite/aiosqlite with PostgreSQL/asyncpg across production (Railway),
local development (Docker), and CI (GitHub Actions service container). No schema
changes — SQLAlchemy ORM is dialect-agnostic.

### Prerequisites

- Docker installed locally (✅ confirmed)
- Railway account with existing project (✅ confirmed)
- No production data to migrate (clean start)

### Implementation Steps

#### Step 1 — Update dependencies

**File:** `requirements.txt`

```diff
- aiosqlite~=0.20
+ asyncpg~=0.30
```

Install and verify:

```bash
pip install -r requirements.txt
```

#### Step 2 — Add `docker-compose.yml` for local PostgreSQL

**File:** `docker-compose.yml` (new, project root)

```yaml
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: adventurer_sheet
      POSTGRES_USER: bot
      POSTGRES_PASSWORD: bot
    ports:
      - "5432:5432"
    tmpfs:
      - /var/lib/postgresql/data
```

**Why `tmpfs`:** Local dev DB is ephemeral — using tmpfs makes Postgres
start faster and avoids cluttering the filesystem with data files. Seed data
can be reloaded with `--seed`.

**Usage:**

```bash
docker compose up -d       # Start Postgres
docker compose down        # Stop and remove
```

#### Step 3 — Update `config.py`

**File:** `src/bot/config.py`

Changes:
- Default `DATABASE_URL` to `postgresql+asyncpg://bot:bot@localhost:5432/adventurer_sheet`
- Add auto-fixup: if `DATABASE_URL` starts with `postgresql://` (Railway's
  format), rewrite to `postgresql+asyncpg://` so SQLAlchemy uses the async driver.

```python
database_url = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://bot:bot@localhost:5432/adventurer_sheet",
).strip()

# Railway provides postgresql:// but SQLAlchemy async needs postgresql+asyncpg://
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
```

#### Step 4 — Update `Dockerfile`

**File:** `Dockerfile`

Changes:
- Remove `RUN mkdir -p /data` (no more SQLite volume)
- Remove `ENV DATABASE_URL=sqlite+aiosqlite:////data/adventurer-sheet.db`
- Railway will inject `DATABASE_URL` from the Postgres plugin automatically

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
COPY src/ src/

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "bot"]
```

#### Step 5 — Update `.env.example`

**File:** `.env.example`

Add `DATABASE_URL` with the local Docker Postgres default:

```dotenv
# Database connection (local Docker Postgres default shown)
DATABASE_URL=postgresql+asyncpg://bot:bot@localhost:5432/adventurer_sheet
```

#### Step 6 — Update test fixtures

**File:** `tests/conftest.py`

Tests will use the same PostgreSQL instance as local dev (via `docker compose`).
The `DATABASE_URL` is read from the environment, falling back to the local
Docker Postgres default. Each test gets a clean database via table drop/recreate.

```python
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://bot:bot@localhost:5432/adventurer_sheet",
)
```

**Why not in-memory?** PostgreSQL has no in-memory mode. Using the same real
engine as production catches dialect-specific issues (e.g. timestamp precision,
constraint naming).

#### Step 7 — Update CI workflow

**File:** `.github/workflows/ci.yml`

Add a PostgreSQL service container and set `TEST_DATABASE_URL`:

```yaml
jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_DB: adventurer_sheet
          POSTGRES_USER: bot
          POSTGRES_PASSWORD: bot
        ports:
          - 5432:5432
        options: >-
          --health-cmd="pg_isready -U bot -d adventurer_sheet"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
    env:
      TEST_DATABASE_URL: postgresql+asyncpg://bot:bot@localhost:5432/adventurer_sheet
    steps:
      # ... existing checkout, setup-python, install, lint, test steps
```

#### Step 8 — Update documentation

**Files:**

| File | Changes |
|------|---------|
| `.github/ARCHITECTURE.md` | Amend ADR-002 and ADR-003 with PostgreSQL migration notes (preserve history) |
| `.github/SETUP.md` | Replace SQLite instructions with `docker compose up -d`; add Railway Postgres provisioning guide |
| `.github/copilot-instructions.md` | Update tech stack from `aiosqlite` to `asyncpg` |

**ADR-002 amendment:**

> **Amendment (Phase 3, Issue #10):** Database switched from SQLite/aiosqlite
> to PostgreSQL/asyncpg. SQLAlchemy ORM abstracted the migration — no schema
> changes were required. PostgreSQL provides proper concurrent access, ACID
> compliance, and is managed by Railway in production.

**ADR-003 amendment:**

> **Amendment (Phase 3, Issue #10):** Database storage moved from a SQLite file
> on a Railway persistent volume to a Railway-managed PostgreSQL instance.
> `DATABASE_URL` is injected by Railway automatically. Local development uses
> Docker Compose to run PostgreSQL. The `/data` volume mount is no longer needed.

**SETUP.md — Railway Postgres provisioning:**

1. Open Railway dashboard → your `adventurer-sheet` project
2. Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
3. Railway creates a Postgres instance and auto-injects `DATABASE_URL` into
   your service's environment variables
4. Verify in **Variables** tab: `DATABASE_URL` should show `postgresql://...`
5. Redeploy — the bot's `config.py` auto-rewrites `postgresql://` to
   `postgresql+asyncpg://`
6. Check Railway logs: should show `Database: postgresql+asyncpg://...`

#### Step 9 — Test and verify

- [ ] `docker compose up -d` starts Postgres locally
- [ ] `pytest --cov` passes with ≥ 80% coverage
- [ ] `ruff check src/ tests/` returns no errors
- [ ] Bot connects to local Postgres: `cd src && python -m bot`
- [ ] All `/character` commands work as before
- [ ] `--seed` flag loads test data into Postgres
- [ ] CI workflow passes with Postgres service container

### Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Railway `DATABASE_URL` format mismatch | Medium | High | Auto-fixup in `config.py` rewrites `postgresql://` → `postgresql+asyncpg://` |
| Tests fail on Postgres-specific behaviour | Low | Medium | Use real Postgres in tests (not SQLite); catches dialect issues early |
| Docker not running when tests run | Medium | Low | Clear error message; document `docker compose up -d` prerequisite |
| CI Postgres service slow to start | Low | Low | Health check with retries in workflow |

---

## Task #11 — Backup Storage

**Issue:** [#11](https://github.com/SiKing/adventurer-sheet/issues/11)
**Branch:** `feat/backup-storage`
**Version bump:** `0.2.1` → `0.2.2`
**Depends on:** #10 (must be on PostgreSQL first)
**Status:** 🔄 In progress

### Summary

Create the ability to back up and restore the production PostgreSQL database.
Backup location must not be local machine or Railway.

### Decision — GitHub Releases

After evaluating options, **GitHub Releases** was chosen:

| Option | Cost | Pros | Cons |
|--------|------|------|------|
| **AWS S3** (free tier) | Free 5GB | Industry standard, boto3 SDK | AWS account setup |
| **Cloudflare R2** | Free 10GB | S3-compatible API, generous free tier | Newer service |
| **Backblaze B2** | Free 10GB | S3-compatible, simple pricing | Less known |
| **GitHub Releases** ✅ | Free | Already have account, zero new infra | Not designed for DB backups |

**Rationale:** Zero cost, zero new accounts, existing GitHub infrastructure.
Backups are stored as pre-release assets to avoid polluting the "latest" release.

### Architecture

**Storage abstraction:** A `BackupStorage` Protocol allows swapping providers
with one new file + one line change. Current adapter: `GitHubReleaseStorage`.

**Naming convention:**
- Filename: `backup-2026-05-01T12-00-00.sql.gz`
- Release tag: `backup/2026-05-01T12-00-00`

**Automation:** GitHub Actions monthly cron (`0 3 1 * *`) + manual
`workflow_dispatch`. Runs `pg_dump` → gzip → upload to GitHub Release.

**Restore:** Manual process — download asset, `gunzip`, `psql < backup.sql`.

### Implementation Steps

#### Step 1 — Storage Protocol

**File:** `src/bot/backup/storage.py` ✅

`BackupStorage` Protocol with three methods:
- `upload(filename, data) → str` (returns download URL)
- `download(filename) → bytes`
- `list_backups() → list[str]`

#### Step 2 — GitHub Releases adapter

**File:** `src/bot/backup/github_storage.py` ✅

`GitHubReleaseStorage` class using `aiohttp` to interact with GitHub API.
Creates pre-release releases with backup files as assets.

#### Step 3 — Backup service

**File:** `src/bot/backup/service.py` ✅

`create_backup(database_url) → (filename, compressed_data)`:
- Normalises URL (`postgresql+asyncpg://` → `postgresql://` for pg_dump)
- Runs `pg_dump` via `asyncio.create_subprocess_exec`
- Returns gzipped SQL dump

#### Step 4 — CLI script and GitHub Actions workflow

**Files:** `scripts/backup.py`, `.github/workflows/backup.yml` ✅

CLI script reads `DATABASE_URL`, `GITHUB_TOKEN`, `GITHUB_REPOSITORY` env vars.
Workflow runs monthly on cron + manual dispatch.

#### Step 5 — Dependencies

**File:** `requirements.txt` ✅

Added `aiohttp~=3.13` for GitHub API calls.

#### Step 6 — Tests

**Files:** `tests/test_backup_service.py`, `tests/test_backup_github_storage.py` ✅

- `TestNormalizeUrl`: 3 pure unit tests ✅
- `TestFilenameToTag`: 4 pure unit tests ✅
- `TestCreateBackup`: 3 integration tests (require `pg_dump` binary)

#### Step 7 — Documentation

Update ARCHITECTURE.md, SETUP.md, copilot-instructions.md with backup details.

### Setup Requirements

1. **GitHub Actions secret:** Add `PROD_DATABASE_URL` (Railway PostgreSQL URL)
   in repo Settings → Secrets → Actions
2. **GitHub token:** Workflow uses `GITHUB_TOKEN` (auto-provided by Actions)

### Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| GitHub Release asset size limit (2 GB) | Low | Low | DB is tiny; monitor growth |
| GitHub API rate limits | Low | Low | One backup/month is well within limits |
| pg_dump version mismatch | Low | Medium | Pin Postgres version in workflow |
| Token permissions | Low | Medium | Workflow uses default `GITHUB_TOKEN` with `contents: write` |

---

## Task #12 — Modify Stats (Incremental Edits)

**Issue:** [#12](https://github.com/SiKing/adventurer-sheet/issues/12)
**Branch:** `feat/modify-stats`
**Version bump:** next patch from main

### Summary

Extend `/character edit <field> <value>` to support incremental value changes
using `+`, `-`, and `=` prefixes. Preserve existing behaviour where a bare
number sets the value directly.

### Value Parsing Rules

| Prefix | Meaning | Example | Result (if current=10) |
|--------|---------|---------|------------------------|
| `+N` | Add N to current value | `+2` | 12 |
| `-N` | Subtract N from current value | `-4` | 6 |
| `=N` | Set to N (explicit absolute) | `=13` | 13 |
| `N` (bare) | Set to N (existing behaviour) | `14` | 14 |

### Implementation Steps

#### Step 1 — Add value parser to `validators.py`

New function: `parse_edit_value(raw: str, current: int) -> int`

- Parses prefix (`+`, `-`, `=`, or bare number)
- Applies the operation against `current`
- Returns the new value
- Raises `InvalidValueError` on non-numeric input

#### Step 2 — Update `repository.py`

`update()` must now receive the current value for integer fields when the
raw input has a `+` or `-` prefix. Modify to fetch the character first (already
does this), then call `parse_edit_value(raw, current)` for integer fields.

#### Step 3 — Update cog

The cog passes the raw string value through to the repository. No cog changes
expected unless the reply message needs to show the delta.

#### Step 4 — Tests

- `test_validators.py`: parametrised tests for `parse_edit_value` covering all
  four prefix cases, boundary values, and invalid input.
- `test_repository.py`: integration tests for incremental updates.
- `test_character_cog.py`: verify the end-to-end flow with mocked repo.

---

## Task #13 — Post Character to Chat

**Issue:** [#13](https://github.com/SiKing/adventurer-sheet/issues/13)
**Branch:** `feat/post-character`
**Version bump:** next patch from main

### Summary

Add `/character post [name]` command that posts the character sheet embed as a
**public** (non-ephemeral) message in the current channel. `name` is optional
and follows active character rules (ADR-007).

### Implementation Steps

#### Step 1 — Add `character_post` command to cog

- Resolve character via `_resolve_or_reply(interaction, name)`
- Build embed with existing `build_character_embed()`
- Reply with `ephemeral=False` (public message)

#### Step 2 — Tests

- `test_character_cog.py`: test happy path (public embed sent), no-name uses
  active character, not-found returns ephemeral error.

### Design Note

This is the simplest task — it reuses the existing embed builder and active
character resolution. The only difference from `/character view` is
`ephemeral=False`.

---

## Task #14 — Combat Scores

**Issue:** [#14](https://github.com/SiKing/adventurer-sheet/issues/14)
**Branch:** `feat/combat-scores`
**Version bump:** next patch from main

### Summary

Enhance the Combat section of the character view embed with class/race-based
defaults, a new `hit_die` column, and reformatted display.

### Changes

#### New column: `hit_die`

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `hit_die` | `Integer` | Not null | Based on `char_class` (see table below) |

**Alembic note:** Since we're on PostgreSQL by this point, we may need a
migration strategy. Options: manual `ALTER TABLE` or introduce Alembic. Decision
to be made when this task begins.

#### Class hit die defaults (5e PHB)

| Class | Hit Die | HP at Level 1 |
|-------|---------|----------------|
| Barbarian | 12 | 12 |
| Bard | 8 | 8 |
| Cleric | 8 | 8 |
| Druid | 8 | 8 |
| Fighter | 10 | 10 |
| Monk | 8 | 8 |
| Paladin | 10 | 10 |
| Ranger | 10 | 10 |
| Rogue | 8 | 8 |
| Sorcerer | 6 | 6 |
| Warlock | 8 | 8 |
| Wizard | 6 | 6 |

**Matching rule:** Use `char_class.lower().startswith(class_name.lower())`
to match. If no match, use current defaults (hit_die=8, max_hp=1).

#### Race speed defaults (5e PHB)

| Race | Speed |
|------|-------|
| Dwarf | 25 |
| Elf | 30 |
| Halfling | 25 |
| Human | 30 |
| Dragonborn | 30 |
| Gnome | 25 |
| Half-Elf | 30 |
| Half-Orc | 30 |
| Tiefling | 30 |

**Matching rule:** Use `race.lower().startswith(race_name.lower())`.
If no match, use default speed of 30.

#### Embed reformat

Rename "Combat" section to "Combat Scores" and reformat:

```
AC 10  ·  Init +0  ·  Speed 30ft
HP 1 / 1  ·  d8
Inspr 0  ·  Prof +2  ·  Percept 10
```

**Note:** "Inspr" refers to inspiration, which is currently not a stored field.
This will need a new column `inspiration` (Integer, default 0) or the display
will show a hardcoded 0. Decision to be confirmed.

### Implementation Steps

#### Step 1 — Add `hit_die` column and class/race defaults module

- New file or section in `validators.py`: `CLASS_DEFAULTS` and `RACE_DEFAULTS`
  lookup tables
- New functions: `default_hit_die(char_class)`, `default_speed(race)`,
  `default_max_hp(hit_die)` (= hit_die value at level 1)

#### Step 2 — Database migration

- Add `hit_die` column to `Character` model
- Add `inspiration` column if confirmed
- Migration strategy TBD (Alembic vs manual ALTER TABLE)

#### Step 3 — Update `repository.py`

- `create()` computes `hit_die`, `speed`, and `max_hp` from class/race defaults
- Add `hit_die` to editable fields

#### Step 4 — Update `embeds.py`

- Rename "Combat" → "Combat Scores"
- Reformat to the specified layout

#### Step 5 — Tests

- Validators: parametrised tests for all 12 classes and 9 races
- Repository: test that create with known class/race sets correct defaults
- Embeds: test new format output

---

## Cross-Cutting Concerns

### ADR-008 Compliance

Every task follows this workflow:

1. Create feature branch from `main`
2. Bump patch version in `pyproject.toml`
3. Implement with TDD (tests first)
4. All tests pass with ≥ 80% coverage
5. `ruff check src/ tests/` clean
6. Update relevant documentation
7. Dependency review (ADR-009) at task completion
8. Merge to `main`

### Documentation Updates

Each task must update:
- `.github/copilot-instructions.md` — if tech stack or project structure changes
- `.github/ARCHITECTURE.md` — if new ADRs or amendments are needed
- `.github/SETUP.md` — if setup steps change
- `README.md` — if user-facing commands change

---

## Success Criteria

Phase 3 is complete when **all** of the following are true:

- [ ] Issue #10: Bot runs on PostgreSQL in production (Railway) and locally (Docker)
- [ ] Issue #11: Database can be backed up and restored from external storage
- [ ] Issue #12: `/character edit` supports `+N`, `-N`, `=N` incremental edits
- [ ] Issue #13: `/character post` sends public embed to channel
- [ ] Issue #14: Combat Scores display class/race defaults with reformatted layout
- [ ] All tasks pass `pytest --cov` with ≥ 80% coverage
- [ ] All tasks pass `ruff check src/ tests/`
- [ ] All documentation is updated and consistent
- [ ] Dependency review completed (ADR-009)

