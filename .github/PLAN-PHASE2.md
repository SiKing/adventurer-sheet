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

**Design choice — simplified creation flow:** `/character create` collects 5
identity fields (name, class, race, background, alignment) via a single Discord
Modal. Level defaults to 1. All ability scores default to 10, AC to 10, speed
to 30 ft, and HP to 1. Users update any of these via `/character edit` after
creation. This keeps the create flow to a single modal within Discord's hard
limit of 5 text inputs.

---

## Architecture Decisions

The architecture decisions made during Phase 2 (ADR-002 through ADR-007) are
documented in [ARCHITECTURE.md](ARCHITECTURE.md).

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
| `level` | `Integer` | Not null, default 1 | Minimum 1; no upper limit enforced |
| `race` | `String(50)` | Not null | |
| `background` | `String(50)` | Not null | |
| `alignment` | `String(20)` | Not null | |
| `strength` | `Integer` | Not null, default 10 | Minimum 1; no upper limit enforced |
| `dexterity` | `Integer` | Not null, default 10 | Minimum 1; no upper limit enforced |
| `constitution` | `Integer` | Not null, default 10 | Minimum 1; no upper limit enforced |
| `intelligence` | `Integer` | Not null, default 10 | Minimum 1; no upper limit enforced |
| `wisdom` | `Integer` | Not null, default 10 | Minimum 1; no upper limit enforced |
| `charisma` | `Integer` | Not null, default 10 | Minimum 1; no upper limit enforced |
| `armor_class` | `Integer` | Not null, default 10 | |
| `speed` | `Integer` | Not null, default 30 | In feet |
| `max_hp` | `Integer` | Not null, default 1 | |
| `current_hp` | `Integer` | Not null, default 1 | |
| `initiative` | `Integer` | Not null, default 0 | Stored; defaults to DEX modifier but player-overridable |
| `proficiency_bonus` | `Integer` | Not null, default 2 | Stored; defaults to `2 + (level-1)//4` but player-overridable |
| `passive_perception` | `Integer` | Not null, default 10 | Stored; defaults to `10 + WIS modifier` but player-overridable |
| `experience_points` | `Integer` | Not null, default 0 | XP total; manually updated by player |
| `created_at` | `DateTime` | Not null, server default `now()` | Set once at insert; never updated |
| `updated_at` | `DateTime` | Not null, server default `now()`, onupdate `now()` | Updated automatically by SQLAlchemy on every `UPDATE`; never set by application code |

**Unique constraint:** `(owner_id, name)` — one user cannot have two characters
with the same name, making `/character view Thorin` unambiguous.

**Default value helpers (used only at creation time, never enforced by DB):**

These Python functions compute the initial default values when a character is
first created. After creation the player can override any of these via
`/character edit`, for example to account for magic items, feats, or class
features that modify the value.

| Field | Initial default formula |
|-------|------------------------|
| `initiative` | `(dexterity - 10) // 2` |
| `proficiency_bonus` | `2 + (level - 1) // 4` |
| `passive_perception` | `10 + (wisdom - 10) // 2` |

> **Why stored, not computed?** A character with *Boots of Speed* or the
> *Alert* feat may have an initiative that no longer matches the raw DEX
> modifier. Storing the value and letting the player override it (Phase 2)
> and eventually auto-update it from equipped items (Phase 3) is the correct
> long-term model.

---

### New file: `src/bot/errors.py`

Custom exception classes:

| Exception | When raised |
|-----------|-------------|
| `CharacterNotFoundError` | Character doesn't exist for this owner |
| `CharacterAlreadyExistsError` | Duplicate `(owner_id, name)` |
| `InvalidFieldError` | Unrecognised or read-only field name in `/character edit` |
| `InvalidValueError` | Value fails validation (e.g. level is zero or negative, HP is zero) |

---

## Command Design

### `/character create`

**Flow:**
1. User types `/character create`.
2. Bot opens a **Modal** with 5 text inputs:
   - Character Name (required, max 100 chars)
   - Class (required, e.g. "Wizard", max 50 chars)
   - Race (required, e.g. "High Elf", max 50 chars)
   - Background (required, e.g. "Sage", max 50 chars)
   - Alignment (required, e.g. "Neutral Good", max 20 chars)
3. On submit: insert the row with level defaulting to 1 and all stat defaults,
   set this character as the active character for the user, reply ephemeral:
   *"✅ **Thorin** has been created and set as your active character! Level defaults to 1 and stats to 10 — use `/character edit` to update them."*
4. On duplicate name: reply ephemeral:
   *"⚠️ You already have a character named **Thorin**."*

---

### `/character view [name]`

**Flow:**
- `name` is optional. If omitted, uses the active character (see ADR-007). If
  no active character is set, replies: *"No active character. Use
  `/character view <name>` or `/character create` to set one."*
- If `name` is provided and the user has no character by that name, replies with
  a not-found error. If omitted with multiple characters and no active set,
  replies: *"You have multiple characters — use `/character list` to see them,
  then `/character view <name>`."*
- Fetches the character via `_get_own_character(interaction, name)`.
- Sets this character as the active character for the user.
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

Footer:  Owned by @username · Updated 2026-04-07
```

> Ability score modifiers (e.g. `+0`, `-1`) are computed for display only
> using `(score - 10) // 2`. Initiative, Proficiency Bonus, and Passive
> Perception are read directly from their stored columns — they reflect
> whatever the player has set, including magic item overrides.

---

### `/character edit [name] <field> <value>`

**Flow:**
- `name` is optional. If omitted, uses the active character (see ADR-007). If
  no active character is set, replies: *"No active character. Use
  `/character view <name>` to set one."*
- `field` uses `app_commands.autocomplete` to suggest the editable field
  names (friendly strings: `strength`, `dexterity`, etc.).
- `value` is a string; validated in Python before any DB write.
- Fetches character via `_get_own_character(interaction, name)`, validates
  value, updates the field.
- Replies ephemeral: *"✅ **Thorin**'s strength updated to 18."*

**Editable fields:** all columns except `id`, `owner_id`, `created_at`, `updated_at`.

> `updated_at` is never accepted as a `/character edit` field. It is set
> automatically by SQLAlchemy's `onupdate=func.now()` on the `UPDATE` statement
> that every `/character edit` call issues — the player cannot read or write it
> directly.

---

### `/character delete <name>`

**Flow:**
- `name` is **always required** — this is a deliberate safety measure to prevent
  accidental deletion of the active character (see ADR-007).
- Fetches character via `_get_own_character(interaction, name)` to confirm
  ownership.
- Replies with an ephemeral `discord.ui.View` containing two buttons:
  - 🗑️ **Yes, delete** — deletes the row; if the deleted character was the
    active character, clears `_active[user_id]`; edits the message to:
    *"🗑️ **Thorin** has been deleted."*
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
- Define `Character` model with all 22 columns and the `(owner_id, name)`
  unique constraint.
- `updated_at` must use `server_default=func.now(), onupdate=func.now()` so
  SQLAlchemy sets it automatically on every `UPDATE` statement — no application
  code ever writes to this column directly.
- Define `get_session_factory(database_url: str) -> async_sessionmaker` which
  calls `create_async_engine` and returns an `async_sessionmaker`.
- Define `create_tables(engine)` coroutine that runs `Base.metadata.create_all`
  (called once at bot startup).

**Tests:** `tests/test_db.py` (in-memory SQLite):
- Model instantiation with all attributes.
- `create_tables` creates the `characters` table.
- Unique constraint raises `IntegrityError` on duplicate `(owner_id, name)`.
- `experience_points` defaults to `0` on a new row.
- `updated_at` changes after an `UPDATE`; `created_at` does not.

**Risk:** Medium — first SQLAlchemy file; column type mistakes are easy. Validate
with `get_errors` after writing.

#### Test data seeding (local development only)

**File:** `tests/seed.py`  *(not under `src/` — never copied into the Docker image)*

**Why `tests/` not `src/`:** The `Dockerfile` only copies `src/` into the
container. Placing `seed.py` under `tests/` guarantees it is physically absent
from the production image — there is no runtime guard required.

**Seed data source — CSV file:** `tests/seed_data.csv`

The CSV file contains one row per character to seed. Columns map directly to the
`characters` table. Any column omitted from the CSV falls back to the same
default used by `/character create` (see Data Model). `owner_id` is a required
column so that multiple owners can be represented — enabling testing of
cross-user access scenarios (e.g. user A trying to view user B's character).

**CSV format:**

```csv
owner_id,name,char_class,race,background,alignment,level,strength,dexterity,constitution,intelligence,wisdom,charisma,armor_class,speed,max_hp,current_hp,initiative,proficiency_bonus,passive_perception,experience_points
111111111111111111,Thorin,Fighter,Dwarf,Soldier,Lawful Good,5,18,10,16,10,12,8,16,25,52,52,0,3,11,6500
111111111111111111,Gandalf,Wizard,Human,Sage,Neutral Good,10,10,14,12,20,18,16,12,30,55,55,2,4,14,64000
222222222222222222,Legolas,Ranger,Elf,Outlander,Chaotic Good,7,12,20,14,14,16,14,15,35,58,58,5,3,13,23000
```

> Multiple `owner_id` values intentionally included so tests can verify that
> user `111111111111111111` cannot access characters owned by `222222222222222222`.

**`seed.py` responsibilities:**

- Read `tests/seed_data.csv` using Python's built-in `csv` module.
- For each row, apply column defaults for any missing or empty fields.
- Call `repository.create(...)` for each row.
- Skip rows where the character already exists (catches `CharacterAlreadyExistsError`).
- Log each inserted/skipped character at INFO level.

**Activation — command-line flag:**

```bash
# Normal start (production and default local)
cd src && python -m bot

# Seed test data then start (local only)
cd src && python -m bot --seed
```

`__main__.py` handles `--seed` as follows:
1. Creates tables (as normal).
2. Dynamically imports `seed` from `tests/seed.py` using `importlib` (so the
   import only happens when the flag is present and fails gracefully if the
   file is absent).
3. Calls `await seed.seed_db(session_factory)`.
4. Logs `"Seed data loaded."` at INFO level.
5. Continues with normal bot startup.

**Production safety:** `tests/seed.py` and `tests/seed_data.csv` are never
copied into the Docker image (`Dockerfile` only copies `src/`). Even if
`--seed` were somehow passed, the dynamic import would fail with a clear
`ModuleNotFoundError` rather than silently succeeding.

**Tests:** `tests/test_seed.py` (in-memory SQLite, reads from `tests/seed_data.csv`):
- `seed_db` inserts one row per CSV row.
- Running `seed_db` twice does not raise an error (idempotent).
- Characters are owned by the `owner_id` values from the CSV.
- Characters with missing optional columns use the expected defaults.

**Risk:** Low — isolated entirely to `tests/`; zero production footprint.

---

### Step 4 — Character repository

**File:** `src/bot/repository.py`

`CharacterRepository` class with `async_sessionmaker` injected in `__init__`:

| Method | Signature | Raises |
|--------|-----------|--------|
| `create` | `(owner_id, name, char_class, level, race, background, alignment) -> Character` — computes and stores initial `initiative`, `proficiency_bonus`, `passive_perception` from level/ability score defaults | `CharacterAlreadyExistsError` |
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

| Function | Purpose |
|----------|---------|
| `validate_level(value: str) -> int` | Integer ≥ 1; no upper limit |
| `validate_ability_score(value: str) -> int` | Integer ≥ 1; no upper limit |
| `validate_positive_int(field: str, value: str) -> int` | Positive integer > 0 |
| `validate_field_name(name: str) -> str` | Must be in editable field set |
| `ability_modifier(score: int) -> int` | `(score - 10) // 2` — used to compute initial defaults at creation time only |
| `proficiency_bonus(level: int) -> int` | `2 + (level - 1) // 4` — used to compute initial default at creation time only |
| `default_passive_perception(wisdom: int) -> int` | `10 + ability_modifier(wisdom)` — used to compute initial default at creation time only |

All raise the appropriate custom exception on invalid input.

**Tests:** `tests/test_validators.py` — parametrised cases covering boundary
values (minimum of 1, zero, negative numbers), empty strings, and non-numeric
strings. No upper-bound tests for level or ability scores.

**Risk:** Low — pure functions are trivial to test.

---

### Step 6 — Embed builder

**File:** `src/bot/embeds.py`

`build_character_embed(character: Character) -> discord.Embed`

Reads all fields directly from the stored `Character` ORM object — no derived
values are computed here. Ability score modifiers (`(score - 10) // 2`) are
computed only for display alongside each ability score in the embed; they are
not stored and not required for any other logic.

**Tests:** `tests/test_embeds.py` — construct a `Character` with known values,
assert title, description, and specific field values in the returned embed.

**Risk:** Low — purely presentational.

---

### Step 7 — Character cog

**File:** `src/bot/cogs/character.py`

Contents:
- `character_group = app_commands.Group(name="character", description="…")`
- `CharacterCog(commands.Cog)` with `CharacterRepository` injected via
  `__init__`, and `_active: dict[str, str]` initialised as an empty dict.
- `_get_own_character(interaction, name)` private helper — resolves `name`
  from `_active` when `None`, raises `CharacterNotFoundError` if unresolvable.
- `_set_active(user_id, name)` and `_clear_active(user_id)` private helpers.
- Five command methods decorated with `@character_group.command(…)`.
- `CreateCharacterModal(discord.ui.Modal)` — 5 text inputs (Name, Class, Race,
  Background, Alignment), `on_submit` handles validation, calls
  `repository.create`, and sets the active character.
- `ConfirmDeleteView(discord.ui.View)` — two buttons, calls `repository.delete`
  on confirm and clears active if the deleted character was active.

**Tests:** `tests/test_character_cog.py` — mock `CharacterRepository` with
`AsyncMock`. Test each command's happy path and all error paths (not found,
already exists, invalid field/value). Active character test cases:
- `/character create` sets active character on success.
- `/character view <name>` sets active character on success.
- `/character view` with no name uses active character.
- `/character view` with no name and no active set returns the helpful prompt.
- `/character edit` with no name uses active character.
- `/character edit` with no name and no active set returns the helpful prompt.
- `/character delete` after confirm clears active if the deleted character was active.
Do not interact with the real Discord API.

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
| `tests/test_seed.py` | Integration | Yes (in-memory, reads `seed_data.csv`) |
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
| `--seed` flag in production | Not possible — `tests/seed.py` and `tests/seed_data.csv` are never copied into the Docker image; dynamic import fails with `ModuleNotFoundError` |

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
| R7 | Active character stale after delete — next command gets `CharacterNotFoundError` | Low | Low | `_clear_active` is called immediately after confirmed delete |
| R8 | Active character reset on bot restart confuses users | Low | Low | Documented as known limitation in ADR-007; users re-activate with `/character view` |

---

## Success Criteria

Phase 2 is complete when **all** of the following are true:

- [ ] `pytest --cov` passes with ≥ 80% coverage across `src/bot/`
- [ ] `ruff check src/ tests/` returns no errors
- [ ] `/character create` opens a modal, saves a character, sets it as active, and replies with confirmation — verified in Discord
- [ ] `/character view <name>` displays a correctly formatted embed and sets the character as active
- [ ] `/character view` with no name uses the active character
- [ ] `/character edit` with no name uses the active character
- [ ] `/character edit <name> strength 18` updates the field; next `/character view` reflects it
- [ ] `/character delete <name>` requires name explicitly, prompts for confirmation, removes the row, and clears active if applicable
- [ ] `/character list` returns only the requesting user's characters
- [ ] A user cannot view or edit another user's character (tested manually with two Discord accounts)
- [ ] Railway redeploy preserves all characters (Volume confirmed working)
- [ ] Bot logs the `DATABASE_URL` at startup (visible in Railway logs)
- [ ] All new source files are ≤ 400 lines

