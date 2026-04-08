# Adventurer Sheet 🎲

A D&D 5e character sheet Discord bot built with Python and discord.py.

## Quick Start

### Prerequisites

- Python 3.12+ (via [pyenv](https://github.com/pyenv/pyenv))
- A Discord Bot Token ([setup guide](.github/PLAN-PHASE1.md#step-2-discord-application-setup))

### Setup

```bash
# Clone the repo
git clone git@github.com:SiKing/adventurer-sheet.git
cd adventurer-sheet

# Install Python 3.12 and create venv
pyenv install 3.12
pyenv local 3.12
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Configure your bot token
cp .env.example .env
# Edit .env and paste your DISCORD_TOKEN
```

### Lint

```bash
ruff check src/ tests/
```

### Run Tests

```bash
pytest
pytest --cov  # with coverage
```

### Run Locally

```bash
cd src
python -m bot
```

The bot will connect to Discord. Try `/about` to verify it's working.

To start with sample characters pre-loaded (local dev only):

```bash
python -m bot --seed
```

`--seed` reads `tests/seed_data.csv` and inserts the rows before the bot connects.
It is idempotent — running it again will not create duplicates. The seed files are
never copied into the Docker image, so this flag has no effect in production.

## Project Structure

```
src/bot/          — Bot source code
src/bot/cogs/     — Discord command modules (one per feature)
tests/            — Test suite
```

## Tech Stack

| Tool | Purpose |
|------|---------|
| discord.py | Discord bot framework |
| python-dotenv | Environment variable loading |
| SQLAlchemy | Database ORM (Phase 2) |
| pytest | Testing |
| ruff | Linting |
| GitHub Actions | CI/CD |
| Railway | Production hosting |

## License

GNU General Public License v3.0 — see [LICENSE.txt](LICENSE.txt) for details.
