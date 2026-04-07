# Phase 2 Plan — Character Sheet Display

> **Goal:** A persistent, per-user D&D 5e character sheet, stored in SQLite,
> displayed as a rich Discord embed, with full CRUD commands and ownership
> security enforced by Discord user ID.

---

## Overview

Phase 2 adds the core value of the bot: users can create, view, edit, delete,
and list their D&D 5e characters entirely through Discord slash commands. Data
is stored in SQLite via SQLAlchemy ORM. Each character is owned by the Discord
user who created it — no user can read or modify another user's sheets.

**Design choice — simplified creation flow:** `/character create` collects only
the 5 identity fields (name, class, level, race, background, alignment) via a
single Discord Modal. All ability scores default to 10, AC to 10, speed to 30 ft,
and HP to 1. Users update stats via `/character edit` after creation. This keeps
the create flow minimal and reduces implementation complexity.

---

## Architecture Decisions

### ADR-002 — Database: SQLite + SQLAlchemy (Async)

**Decision:** Use SQLite as the database engine with SQLAlchemy's **async** ORM
(`create_async_engine`, `async_sessionmaker`), backed by the `aiosqlite` driver.

**Rationale:** SQLite requires zero infrastructure — it is a single file on
disk, which maps directly to Railway's persistent volume model. SQLAlchemy's
ORM gives type-safe, injection-proof queries and a clear migration path to
PostgreSQL later. The **async** API is mandatory because discord.py runs on an
asyncio event loop; a blocking synchronous DB call would freeze the bot for all
users while the query runs.

**Alternatives rejected:**
- Raw `sqlite3` module — synchronous, no injection protection, no migration path.
- Sync SQLAlchemy in `run_in_executor` — works but adds indirection; async
  SQLAlchemy is now stable and is the correct choice.
- PostgreSQL — unnecessary operational overhead for a single-instance bot.

---

### ADR-003 — Database File Location in Production

**Decision:** Store the SQLite file at the path given by the `DATABASE_URL`
environment variable, defaulting to `sqlite+aiosqlite:////data/adventurer-sheet.db`.

**Rationale (ADR-001 compliance):** The Docker container filesystem is
ephemeral. Every redeploy resets it to exactly what the `Dockerfile` copied in.
Any `.db` file written to `/app` at runtime is **lost on the next deploy**.

**Railway Volume:** Railway allows attaching a persistent Volume to a service,
mounted at a chosen path (e.g. `/data`). The volume survives deploys and
restarts. By pointing `DATABASE_URL` at `/data/adventurer-sheet.db`, the
database is durable.

**Local development:** `DATABASE_URL` defaults to
`sqlite+aiosqlite:///./characters.db` (relative path, current directory). No
code change is needed between environments — only the env var differs.

---

### ADR-004 — Cog Structure: One `CharacterCog` with a Command Group

**Decision:** All character commands live in `src/bot/cogs/character.py`, using
an `app_commands.Group(name="character")`.

**Rationale:** All five commands share the same repository and ownership-check
helper. One cog means one `load_extension` call, one injected dependency, and
one private ownership helper. If the cog exceeds ~400 lines in Phase 3, it can
be split without changing any user-visible command names.

---

### ADR-005 — Discord UX: Single Modal for Character Creation

**Decision:** `/character create` opens a single Discord Modal with 5 identity
fields. All stat fields default to safe baseline values and are editable via
`/character edit` after creation.

**Rationale:** Discord Modals support up to 5 text inputs. Collecting 15+ fields
across 3 sequential modals is technically possible but creates confusing UX for
new users. Starting with just the identity fields and sensible defaults is faster
to create a character, easier to implement correctly, and simpler to test.
Detailed stats can be filled in at the user's own pace with `/character edit`.

---

### ADR-006 — Security: Ownership Enforcement

**Decision:** Every command that reads or modifies a character calls a private
`_get_own_character(interaction, name)` helper. This queries
`WHERE name = ? AND owner_id = ?`. If no row is found, it raises
`CharacterNotFoundError`. The command catches this and replies with an ephemeral
(private) error message.

**Why this is safe:** `owner_id` is always set from `interaction.user.id` — a
value supplied by Discord's gateway, not typed by the user. A user cannot forge
it. All queries use SQLAlchemy parameters (never string formatting), preventing
SQL injection. A correctly named character belonging to another user will never
be returned.

---

## Data Model

### New file: `src/bot/db.py`

Owns the SQLAlchemy engine setup, the `Character` ORM model, and the
`get_session_factory` function.

**Table: `characters`**

| Column | SQLAlchemy Type | Constraints | Notes |
|--------|----------------|-------------|-------|
| `id` | `Integer` | Primary key, autoincrement | Internal row ID |
| `owner_id` | `String(32)` | Not null, indexed | Discord user ID (string to avoid integer overflow) |
| `name` | `String(100)` | Not null | Character name |
| `char_class` | `String(50)` | Not null | `class` is a Python keyword — column named `char_class` |
| `level` | `Integer` | Not null, default 1 | 1–20 |
| `race` | `String(50)` | Not null | |
| `background` | `String(50)` | Not null | |
| `alignment` | `String(20)` | Not null | |
| `strength` | `Integer` | Not null, default 10 | 1–20 |
| `dexterity` | `Integer` | Not null, default 10 | 1–20 |
| `constitution` | `Integer` | Not null, default 10 | 1–20 |
| `intelligence` | `Integer` | Not null, default 10 | 1–20 |
| `wisdom` | `Integer` | Not null, default 10 | 1–20 |
| `charisma` | `Integer` | Not null, default 10 | 1–20 |
| `armor_class` | `Integer` | Not null, default 10 | |
| `speed` | `Integer` | Not null, default 30 | In feet |
| `max_hp` | `Integer` | Not null, default 1 | |
| `current_hp` | `Integer` | Not null, default 1 | |
| `created_at` | `DateTime` | Not null, server default `now()` | Audit timestamp |

**Unique constraint:** `(owner_id, name)` — one user cannot have two characters
with the same name, making `/character view Thorin` unambiguous.

**Derived values (computed in Python, never stored):**

| Value | Formula |
|-------|---------|
| Ability modifier | `(score - 10) // 2` |
| Initiative | DEX modifier |
| Proficiency bonus | `2 + (level - 1) // 4` |
| Passive Perception | `10 + WIS modifier` |

---

### New file: `src/bot/errors.py`

Custom exception classes:

| Exception | When raised |
|-----------|-------------|
| `CharacterNotFoundError` | Character doesn't exist for this owner |
| `CharacterAlreadyExistsError` | Duplicate `(owner_id, name)` |
| `InvalidFieldError` | Unrecognised or read-only field name in `/character edit` |
| `InvalidValueError` | Value fails validation (e.g. level > 20) |

---

## Command Design

### `/character create`

**Flow:**
1. User types `/character create`.
2. Bot opens a **Modal** with 6 text fields:
   - Character Name (required, max 100 chars)
   - Class (required, e.g. "Wizard", max 50 chars)
   - Level (required, e.g. "5", max 2 chars)
   - Race (required, e.g. "High Elf", max 50 chars)
   - Background (required, e.g. "Sage", max 50 chars)
   - Alignment (required, e.g. "Neutral Good", max 20 chars)
3. On submit: validate level (integer 1–20), insert the row with all stat
   defaults, reply ephemeral:
   *"✅ **Thorin** has been created! All stats default to 10 — use `/character edit` to update them."*
4. On duplicate name: reply ephemeral:
   *"⚠️ You already have a character named **Thorin**."*

---

### `/character view [name]`

**Flow:**
- `name` is optional. If omitted and the user has exactly one character, show
  it. If omitted with multiple, reply: *"You have multiple characters — use
  `/character list` to see them, then `/character view <name>`."*
- Fetches the character via `_get_own_character(interaction, name)`.
- Replies with a rich `discord.Embed`.

**Embed layout:**
```
Title:        ⚔️ Thorin Oakenshield
Color:        discord.Color.dark_gold()
Description:  Dwarf Fighter (Level 5) · Soldier · Lawful Good

Fields (inline, 3 per row):
  STR  10 (+0)  |  DEX  10 (+0)  |  CON  10 (+0)
  INT  10 (+0)  |  WIS  10 (+0)  |  CHA  10 (+0)

  AC  10  |  Speed  30 ft  |  HP  1 / 1

  Initiative: +0  |  Proficiency: +2  |  Passive Perception: 10

Footer:  Owned by @username · Created 2026-04-07
```

---

### `/character edit <name> <field> <value>`

**Flow:**
- `field` uses `app_commands.autocomplete` to suggest the 14 editable field
  names (friendly strings: `strength`, `dexterity`, etc.).
- `value` is a string; validated in Python before any DB write.
- Fetches character, validates value, updates the field.
- Replies ephemeral: *"✅ **Thorin**'s strength updated to 18."*

**Editable fields:** all columns except `id`, `owner_id`, `created_at`.

---

### `/character delete <name>`

**Flow:**
- Fetches character via `_get_own_character` to confirm ownership.
- Replies with an ephemeral `discord.ui.View` containing two buttons:
  - 🗑️ **Yes, delete** — deletes the row, edits the message to confirm.
  - ✖ **Cancel** — edits the message to *"✖ Deletion cancelled."*
- Buttons time out after 60 seconds (treated as Cancel).

---

### `/character list`

**Flow:**
- Queries all characters `WHERE owner_id = ?`, ordered by `name ASC`.
- If none: *"You don't have any characters yet. Use `/character create` to make one!"*
- Otherwise: ephemeral embed listing each as one line:
  `• Thorin — Dwarf Fighter Lv.5`

---

## Implementation Steps

Complete and verify tests for each step before starting the next.

---

### Step 1 — Add dependencies

**File:** `requirements.txt`

Add:
```
sqlalchemy~=2.0
aiosqlite~=0.20
```

**Why:** SQLAlchemy 2.0 is the current stable release with first-class async
support. `aiosqlite` is the async SQLite driver SQLAlchemy requires.

**Risk:** Low.

---

### Step 2 — Custom exceptions

**File:** `src/bot/errors.py`

Define the four exception classes listed in the Data Model section.

**Tests:** `tests/test_errors.py` — assert each is a subclass of `Exception`
and can be raised and caught.

**Risk:** Low.

---

### Step 3 — Database module

**File:** `src/bot/db.py`

- Define SQLAlchemy `Base` (declarative base).
- Define `Character` model with all 19 columns and the `(owner_id, name)`
  unique constraint.
- Define `get_session_factory(database_url: str) -> async_sessionmaker` which
  calls `create_async_engine` and returns an `async_sessionmaker`.
- Define `create_tables(engine)` coroutine that runs `Base.metadata.create_all`
  (called once at bot startup).

**Tests:** `tests/test_db.py` (in-memory SQLite):
- Model instantiation with all attributes.
- `create_tables` creates the `characters` table.
- Unique constraint raises `IntegrityError` on duplicate `(owner_id, name)`.

**Risk:** Medium — first SQLAlchemy file; column type mistakes are easy. Validate
with `get_errors` after writing.

---

### Step 4 — Character repository

**File:** `src/bot/repository.py`

`CharacterRepository` class with `async_sessionmaker` injected in `__init__`:

| Method | Signature | Raises |
|--------|-----------|--------|
| `create` | `(owner_id, name, char_class, level, race, background, alignment) -> Character` | `CharacterAlreadyExistsError` |
| `get_by_name` | `(owner_id, name) -> Character` | `CharacterNotFoundError` |
| `list_by_owner` | `(owner_id) -> list[Character]` | — |
| `update` | `(owner_id, name, field, value) -> Character` | `CharacterNotFoundError`, `InvalidFieldError`, `InvalidValueError` |
| `delete` | `(owner_id, name) -> None` | `CharacterNotFoundError` |

**Tests:** `tests/test_repository.py` using a shared `session_factory` fixture
(in-memory SQLite). Test every method including all error paths.

**Risk:** Medium — async session management has subtle rules. Always use
`async with session_factory() as session:`.

---

### Step 5 — Validation helpers

**File:** `src/bot/validators.py`

Pure functions (no I/O, no Discord, no DB):

| Function | Validates |
|----------|-----------|
| `validate_level(value: str) -> int` | Integer 1–20 |
| `validate_ability_score(value: str) -> int` | Integer 1–20 |
| `validate_positive_int(field: str, value: str) -> int` | Positive integer > 0 |
| `validate_field_name(name: str) -> str` | Must be in editable field set |
| `ability_modifier(score: int) -> int` | `(score - 10) // 2` |
| `proficiency_bonus(level: int) -> int` | `2 + (level - 1) // 4` |

All raise the appropriate custom exception on invalid input.

**Tests:** `tests/test_validators.py` — parametrised cases covering boundary
values, empty strings, and non-numeric strings.

**Risk:** Low — pure functions are trivial to test.

---

### Step 6 — Embed builder

**File:** `src/bot/embeds.py`

`build_character_embed(character: Character) -> discord.Embed`

Reads all fields from the ORM object, computes derived values via
`validators.py`, and constructs the embed described in the Command Design
section above.

**Tests:** `tests/test_embeds.py` — construct a `Character` with known values,
assert title, description, and specific field values in the returned embed.

**Risk:** Low — purely presentational.

---

### Step 7 — Character cog

**File:** `src/bot/cogs/character.py`

Contents:
- `character_group = app_commands.Group(name="character", description="…")`
- `CharacterCog(commands.Cog)` with `CharacterRepository` injected via
  `__init__`.
- `_get_own_character(interaction, name)` private helper.
- Five command methods decorated with `@character_group.command(…)`.
- `CreateCharacterModal(discord.ui.Modal)` — 6 text inputs, `on_submit` handles
  validation and calls `repository.create`.
- `ConfirmDeleteView(discord.ui.View)` — two buttons, calls `repository.delete`
  on confirm.

**Tests:** `tests/test_character_cog.py` — mock `CharacterRepository` with
`AsyncMock`. Test each command's happy path and all error paths (not found,
already exists, invalid field/value). Do not interact with the real Discord API.

**Risk:** High — most complex file. Write test skeletons first (TDD), then
implement.

---

### Step 8 — Wire up in `config.py` and `__main__.py`

**Files:** `src/bot/config.py`, `src/bot/__main__.py`

`config.py` changes:
- Read `DATABASE_URL`; default to `sqlite+aiosqlite:///./characters.db`.
- Add to the returned config dict.

`__main__.py` changes:
- Call `get_session_factory(config["DATABASE_URL"])` at startup.
- Call `create_tables(engine)` before loading cogs (tables must exist before
  the cog tries to query them).
- Pass `session_factory` into `CharacterCog(bot, session_factory)`.
- Add `await bot.load_extension("bot.cogs.character")` / register cog.

**Tests:** Update `tests/test_config.py` — assert `DATABASE_URL` is returned,
and falls back correctly when the env var is absent.

**Risk:** Low — small, targeted changes to already-tested files.

---

### Step 9 — Dockerfile and Railway volume

**File:** `Dockerfile`

Add `RUN mkdir -p /data` and set the default `DATABASE_URL` env var:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /data
COPY pyproject.toml .
COPY src/ src/
ENV PYTHONPATH=/app/src
ENV DATABASE_URL=sqlite+aiosqlite:////data/adventurer-sheet.db
CMD ["python", "-m", "bot"]
```

Note: four slashes in the URL = three from SQLAlchemy's `sqlite:///` prefix +
one for the absolute path `/data/…`.

**Railway Volume setup (manual — one-time):**
1. Railway dashboard → service → **Volumes** tab.
2. Add volume, mount path: `/data`.
3. Verify `DATABASE_URL` env var is set (or rely on the Dockerfile default).

**Risk:** Medium — if the volume is not configured, characters are lost on
redeploy. The bot should log the `DATABASE_URL` at startup so this is
immediately visible in Railway logs.

---

## Testing Strategy

| File | Type | Uses real SQLAlchemy? |
|------|------|-----------------------|
| `tests/conftest.py` | Shared fixtures | Yes (in-memory) |
| `tests/test_errors.py` | Unit | No |
| `tests/test_db.py` | Integration | Yes |
| `tests/test_repository.py` | Integration | Yes |
| `tests/test_validators.py` | Unit | No |
| `tests/test_embeds.py` | Unit | No |
| `tests/test_character_cog.py` | Unit | No (mock repo) |

### Shared fixture (`tests/conftest.py`)

An async `session_factory` fixture that:
1. Creates an async in-memory engine: `"sqlite+aiosqlite:///:memory:"`.
2. Runs `create_tables(engine)`.
3. Yields the `async_sessionmaker`.
4. Drops all tables after each test.

### Coverage target

80% across `src/bot/` (already enforced by `pyproject.toml`). The character
cog is the most complex file — aim for 90%+ there by testing all branches.

---

## Production Considerations

| Concern | Action |
|---------|--------|
| Database persistence | Configure Railway Volume at `/data` before first deploy |
| `DATABASE_URL` | Set in Railway environment variables (or rely on Dockerfile default) |
| Table creation | Handled automatically at bot startup via `create_tables` — no migration tool needed for Phase 2 |
| Log the DB path | Add `logger.info("Database: %s", config["DATABASE_URL"])` in `__main__.py` |
| Characters lost after redeploy | Root cause: Volume not attached. Fix: attach volume in Railway dashboard |

---

## Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R1 | Railway Volume not configured — DB lost on redeploy | Medium | High | Document setup; bot logs DB path at startup |
| R2 | Async session not closed — resource leak | Medium | Medium | Always use `async with session_factory() as session:` in repository |
| R3 | Discord Modal `on_submit` called with empty field values | Low | Low | Discord enforces `required=True` on modal fields server-side |
| R4 | `/character` command group not synced after first deploy | Low | High | `bot.tree.sync()` already called in `on_ready`; confirm in logs |
| R5 | 80% coverage threshold not met for cog | Medium | Low | Write test skeletons before implementing cog (TDD) |
| R6 | `create_all` at startup alters existing prod schema | Low | High | `create_all` only adds missing tables; never drops or alters columns |

---

## Success Criteria

Phase 2 is complete when **all** of the following are true:

- [ ] `pytest --cov` passes with ≥ 80% coverage across `src/bot/`
- [ ] `ruff check src/ tests/` returns no errors
- [ ] `/character create` opens a modal, saves a character, and replies with confirmation — verified in Discord
- [ ] `/character view <name>` displays a correctly formatted embed with derived values
- [ ] `/character edit <name> strength 18` updates the field; next `/character view` reflects it
- [ ] `/character delete <name>` prompts for confirmation and removes the row
- [ ] `/character list` returns only the requesting user's characters
- [ ] A user cannot view or edit another user's character (tested manually with two Discord accounts)
- [ ] Railway redeploy preserves all characters (Volume confirmed working)
- [ ] Bot logs the `DATABASE_URL` at startup (visible in Railway logs)
- [ ] All new source files are ≤ 400 lines

