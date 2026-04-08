# Architecture Decisions

Standing rules and principles that apply to all current and future development.

---

## ADR-001: Production-First Command Design

**Date:** 2026-04-07

### Rule

When designing and implementing any bot command, **production environment is the primary target**.
Local development mode is secondary. When it is possible for both to behave identically,
that is preferred — but production correctness always wins when there is a trade-off.

### Rationale

The production environment (Railway, Docker) differs from a local checkout in important ways:

- Only files explicitly copied in the `Dockerfile` exist at runtime
- There is no project source tree, no `pyproject.toml`, no `requirements*.txt` unless added
- File system paths that work locally will silently fail in the container

A command that works locally but silently returns wrong data in production is worse than one
that fails loudly, because the bug may go unnoticed.

### Practical implications

| Concern | Correct approach |
|---------|-----------------|
| Reading project metadata (version, description) | Copy the file into the Docker image, or inject values as environment variables at build time |
| File paths | Never assume a file exists unless it is explicitly `COPY`-ed in the `Dockerfile` |
| Environment variables | Define all required vars in `.env.example`; document them; validate at startup |
| External services (DB, API) | Design and test against the production service first; mock only in unit tests |
| Secrets | Always via environment variables — never hardcoded, never read from a local file |

### Example: `/about` command lesson

The initial implementation of `/about` read `pyproject.toml` at runtime using a relative
path. This worked locally but returned `"unknown"` for both version and description in
production because `pyproject.toml` was not copied into the Docker image.

**Fix:** Add `COPY pyproject.toml .` to the `Dockerfile` so the file is available in the
container at the same relative path that the code expects.

---

## ADR-002: Database — SQLite + SQLAlchemy (Async)

**Date:** 2026-04-07

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
- Sync SQLAlchemy in `run_in_executor` — works but adds indirection; async SQLAlchemy is now stable.
- PostgreSQL — unnecessary operational overhead for a single-instance bot.

---

## ADR-003: Database File Location in Production

**Date:** 2026-04-07

**Decision:** Store the SQLite file at the path given by the `DATABASE_URL`
environment variable, defaulting to `sqlite+aiosqlite:////data/adventurer-sheet.db`.

**Rationale (ADR-001 compliance):** The Docker container filesystem is ephemeral.
Any `.db` file written to `/app` at runtime is **lost on the next deploy**.

**Railway Volume:** Attach a persistent Volume mounted at `/data`. The volume
survives deploys and restarts. Point `DATABASE_URL` at `/data/adventurer-sheet.db`.

**Local development:** `DATABASE_URL` defaults to `sqlite+aiosqlite:///./characters.db`
(relative path, current directory). No code change needed between environments.

---

## ADR-004: Cog Structure — One `CharacterCog` with a Command Group

**Date:** 2026-04-07

**Decision:** All character commands live in `src/bot/cogs/character.py`, using
an `app_commands.Group` defined as a **class-level attribute** on `CharacterCog`.

**Rationale:** All five commands share the same repository and ownership-check
helper. One cog means one `load_extension` call, one injected dependency, and
one private ownership helper. The group must be a cog class attribute (not a
module-level variable) so that discord.py correctly binds `self` on all
sub-command callbacks during dispatch — a module-level group added via
`bot.tree.add_command()` will cause `CommandSignatureMismatch` errors at runtime.

---

## ADR-005: Discord UX — Single Modal for Character Creation

**Date:** 2026-04-07

**Decision:** `/character create` opens a single Discord Modal with **5 text
inputs**: Name, Class, Race, Background, and Alignment. Level defaults to 1
and is set via `/character edit` after creation.

**Rationale:** Discord enforces a hard limit of **5 `TextInput` components per
Modal**. Rather than split creation across two sequential modals (confusing UX)
or force all fields as slash command options (poor UX beyond ~5 options), Level
is dropped from the modal and defaults to 1. It is the first thing a player
edits after creation.

---

## ADR-006: Security — Ownership Enforcement

**Date:** 2026-04-07

**Decision:** Every command that reads or modifies a character calls a private
`_get_own_character(interaction, name)` helper. This queries
`WHERE name = ? AND owner_id = ?`. If no row is found it raises
`CharacterNotFoundError`; the command catches this and replies ephemeral.

**Why this is safe:** `owner_id` is always set from `interaction.user.id` — a
value supplied by Discord's gateway, not typed by the user. All queries use
SQLAlchemy parameters (never string formatting), preventing SQL injection.

---

## ADR-007: Active Character — In-Memory Per-User Session State

**Date:** 2026-04-07

**Decision:** `CharacterCog` maintains `_active: dict[str, str]` mapping each
Discord user ID to their currently active character name. **Not persisted.**

**Set by:** `/character create` (on success) and `/character view` (on success).

**Read by:** `_get_own_character(interaction, name)` — if `name` is `None`,
looks up `_active.get(user_id)`. Replies ephemeral if no active character is set.

**Cleared by:** `/character delete` — after confirmed delete, removes the entry
from `_active` if the deleted character was the active one.

**Commands where `name` is optional (defaults to active):**
- `/character view [name]`
- `/character edit [name] <field> <value>`

**Commands where `name` is always required:**
- `/character delete <name>` — required as a deliberate safety measure to
  prevent accidental deletion of the active character.

**Rationale for in-memory:** The active character is a convenience shortcut, not
persistent user data. It is naturally session-scoped — losing it on bot restart
is acceptable (the user simply views a character again to restore it). A
database-backed approach adds a new table, repository methods, and tests for
marginal UX gain. Can be revisited in a future phase if user feedback shows the
reset on restart is disruptive.

**Known limitation:** State resets on every bot restart or Railway redeploy.
This is documented behaviour, not a bug.

---

## ADR-008: Git Workflow Rules

**Date:** 2026-04-07

### Rules

1. **One git operation at a time.** Never chain git commands with `&&` or `;`.
   Each operation (create branch, stage files, commit, push) is executed
   separately so the developer retains full control over what runs and when.

2. **Bump the patch version on every new feature branch.** When creating a new
   branch, increment the patch version in `pyproject.toml`
   (`MAJOR.MINOR.PATCH`) and include it in the first commit on that branch.
   This keeps the deployed version traceable to the branch that produced it.

### Branch naming conventions

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feat/` | New feature | `feat/character-sheet` |
| `fix/` | Bug fix | `fix/about-command-production` |
| `docs/` | Documentation only | `docs/phase2-plan` |
| `ci/` | CI/CD changes | `ci/run-on-all-branches` |
| `refactor/` | Code restructure, no behaviour change | `refactor/extract-validators` |

### Version bump rule

```toml
# pyproject.toml — bump patch when creating a new branch
[project]
version = "0.1.2"   # was 0.1.1 on main
```

The patch version is incremented once per branch, in the first commit,
regardless of how many changes are made on that branch.

---

## ADR-009: Dependency Review at Plan Completion

**Date:** 2026-04-07

### Rule

When all steps of a Plan have been completed and tests are passing, **check for
newer versions of every package in `requirements.txt` and `requirements-dev.txt`**
before merging the branch. Update packages that have safe upgrades available;
document any that are intentionally held back.

### Rationale

Feature branches take time. A package that was current at the start of a plan
may have received bug fixes, security patches, or compatible minor releases by
the time the branch is ready to merge. Reviewing at plan completion creates a
consistent, low-effort cadence that keeps dependencies fresh without disrupting
active development.

### Process

Run the following at the end of every plan:

```bash
pip list --outdated
```

For each outdated package, apply this decision table:

| Package type | Condition | Action |
|--------------|-----------|--------|
| `requirements-dev.txt` (tool) | New version available | Upgrade and re-run lint + tests; update the pin |
| `requirements.txt` (runtime, `~=` pin) | New patch/minor within the pinned range | `pip install --upgrade <pkg>` to verify; update pin range if needed |
| `requirements.txt` (runtime) | New **major** version | Treat as a planned upgrade: read changelog, write a dedicated `fix/` or `feat/` branch |
| Any package | Known breaking change or incompatibility | Hold back; add a comment in the requirements file explaining why |

### Holdback comment format

```
# discord.py~=2.4  # held at 2.x — 3.0 has breaking slash-command API changes
discord.py~=2.4
```

### What "safe upgrade" means

- **`requirements-dev.txt`:** Any new version is worth testing. These packages
  do not ship to production; the only risk is a lint rule change or a test
  runner behavioural difference — both caught immediately by CI.
- **`requirements.txt`:** Patch and minor upgrades within the `~=` range are
  safe by definition (semantic versioning). Major upgrades require a changelog
  review and dedicated branch.

### Example: Phase 2 lesson

`ruff` was unpinned in `requirements-dev.txt`. CI installed a newer version that
flagged an import-sorting error that the local version silently accepted. The fix
was to pin `ruff==0.15.9`. A dependency review at Phase 2 completion would have
caught this proactively.
