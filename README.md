# Adventurer Sheet 🎲

A D&D 5e character sheet Discord bot built with Python and discord.py.

## Quick Start

### Prerequisites

- Python 3.12+ (via [pyenv](https://github.com/pyenv/pyenv))
- A Discord Bot Token ([setup guide](.github/PLAN-PHASE1.md#step-2-discord-application-setup))

### Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/adventurer-sheet.git
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

### Run Locally

```bash
cd src
python -m bot
```

The bot will connect to Discord and respond to `/hello`.

### Run Tests

```bash
pytest
pytest --cov  # with coverage
```

### Lint

```bash
ruff check src/ tests/
```

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

Private project.

