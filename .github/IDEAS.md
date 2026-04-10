# Adventurer Sheet — D&D 5e Character Sheet Discord Bot

I want to create a Discord app that will be able to show a Dungeons and Dragons 5e character sheet.
I want to use Python and discord.py. At this time I am not familiar with Python, but I do have a background in programming. I will rely on you to make architectural decisions, with some explanation why a particular decision was made. When making architectural decisions, consider future expansion based on the following information.

The project will be broken up into 3 very broad phases.

---

## Decisions & Constraints

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Project name** | `adventurer-sheet` | Descriptive, clean GitHub repo name |
| **Language** | Python 3.12 (via `brew install python@3.12`) | Stable, great type hints, no admin needed |
| **Bot framework** | discord.py | Mature, well-documented, async-native |
| **Database** | SQLite + SQLAlchemy ORM | Zero setup, identical local/prod, file-based; SQLAlchemy allows future DB swap |
| **Hosting (prod)** | Railway.app | Simplest option, free tier, deploy from GitHub |
| **Hosting (dev)** | Local machine | Bot connects outbound to Discord gateway — no tunneling needed |
| **CI/CD** | GitHub Actions | Free for public repos, natural fit with GitHub |
| **Python env** | pyenv (via brew) + venv | Per-project Python version, no admin needed |
| **Admin access** | Not available | All tooling chosen to work without admin/root |
| **Existing tools** | Homebrew 5.1.3, Python 3.9 (system), Git | Will use brew to bootstrap pyenv + Python 3.12 |
| **Discord server** | Existing test server ready | No setup needed |
| **Discord Application** | Not yet created | Phase 1 plan includes step-by-step setup |
| **Scaling priority** | Low usage, simplicity first | No need for horizontal scaling or managed DBs |

---

## Phase 1: Hello World — Full Pipeline

Start with creating a new GitHub project, guide me to set up all other accounts that will be required for hosting this app.

Create a trivial "Hello world!" app that goes through the entire workflow of checking in code, build, deploy, publish, and finally verify on my personal Discord server.

## Phase 2: Character Sheet Display

Modify the app so that it displays a character sheet.

In this phase, everything will be manually entered by the end-user. An existing Discord account is a prerequisite.

Incorporate security: each end-user can see and modify only character sheets they have created. This will be based on Discord user ID?

## Phase 3: Additional Features

Will create additional features to be determined at a later time.

Phase 3 will be divided into individual tasks. Each task should be treated as a separate new feature.

### TASK-001: Persistent storage

Switch the database to PostgreSQL (free on Railway) Railway provides a free managed PostgreSQL instance. This would require:

- Changing DATABASE_URL to a postgresql+asyncpg://... connection string
- Adding asyncpg to requirements.txt, removing aiosqlite
- No schema changes needed — SQLAlchemy handles both dialects identically
- Railway injects DATABASE_URL automatically when you provision a Postgres plugin
- Update all documentation. Historical documentation should not be deleted only amended. Make sure to include any new setup steps that must be performed.

### TASK-002: Backup storage

Create the ability to back up and restore the production database.

The backup location should **not** be local machine, or Railway. Suggest comparison of some options.

### TASK-003: Modify stats

Currently I am able to edit stats only by entering a new value. This is accomplished with the command `/character edit <field> <value>`.
I want to be able to modify stats by entering an "incremental value". Entering value "+2" would increase the specified value by 2. I want to also be able to enter negative numbers to decrease a value. For sake of consistency I want to be able to enter "=10" which would set the current value to 10.

Preserve existing functionality, where entering a value with no symbol just sets the current value to the number entered.

Here are some examples that modify the strength field, using `/character edit strength <entered_value>`:

| current strength | entered value | new strength |
|------------------|---------------|--------------|
| 10               | +2            | 12           |
| 12               | -4            | 8            |
| 8                | =13           | 13           |
| 13               | 14            | 14           |


### TASK-004: Post character to chat

I want to have the ability to post my character sheet to current chat.
This should be done with the command `/character post <name>`, where name is optional and follows established rules for active character.

### TASK-005: Combat Scores

This one task is several smaller sub-tasks. All of these sub-tasks deal with the "Combat" block in `/character view`.

Rename "Combat" to "Combat Scores".

Reformat the block display according to the following:
.........1.........2.........3.......
```
AC 10  ·  Init +0  ·  Speed 30ft
HP 1 / 1  ·  d8
Inspr +1  ·  Prof +2  ·  Percept 10
```

### Tasks still under consideration

- Realign combat scores.
- Default combat scored.
- Link Combat scores.
- Create page 2: skills and feats
- Create page 3: spells
- Automatically update stats based on level progression.
- Automatically update stats based on new skills, feats, etc.
- Retrieve descriptions of skills, feats, spells, etc. using REST calls to dnd5eapi.com
