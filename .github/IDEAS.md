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

Will create additional features as needed.

Phase 3 will be divided into individual tasks. Each task should be treated as a separate new feature. Make sure ADR-008 is followed for each task, and that all documentation is updated accordingly.

I have moved all tasks from here to the Issues section of the GitHub repo.

### Tasks still under consideration

- Create page 2: skills and feats
- Create page 3: spells
- Automatically update stats based on level progression.
- Automatically update stats based on new skills, feats, etc.
- Retrieve descriptions of skills, feats, spells, etc. using REST calls to dnd5eapi.com
