# Developer Setup Guide

Quick setup instructions for cloning and running the Adventurer Sheet bot on a new machine.

---

## Prerequisites

- Git with SSH keys configured for GitHub
- A terminal (bash or zsh)
- Your Discord bot token (from [discord.com/developers](https://discord.com/developers))

---

## macOS Setup (with Homebrew)

```bash
# 1. Clone the repo
git clone git@github.com:SiKing/adventurer-sheet.git
cd adventurer-sheet

# 2. Install pyenv and xz (for lzma support)
brew install pyenv xz

# 3. Add pyenv to your shell (add to ~/.bash_profile or ~/.zshrc)
cat >> ~/.bash_profile << 'EOF'

# pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOF
source ~/.bash_profile

# 4. Install Python 3.12 and create venv
pyenv install 3.12
pyenv local 3.12
python -m venv .venv
source .venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 6. Create .env with your bot token
cp .env.example .env
# Edit .env and paste your DISCORD_TOKEN

# 7. Run tests
pytest -v

# 8. Run the bot
cd src
python -m bot
```

---

## Linux Setup (without Homebrew)

```bash
# 1. Clone the repo
git clone git@github.com:SiKing/adventurer-sheet.git
cd adventurer-sheet

# 2. Install pyenv (installs to ~/.pyenv, no admin needed)
curl https://pyenv.run | bash

# 3. Add pyenv to your shell (add to ~/.bashrc or ~/.zshrc)
cat >> ~/.bashrc << 'EOF'

# pyenv
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOF
source ~/.bashrc

# 4. Install Python build dependencies (requires sudo)
#    Ubuntu/Debian:
sudo apt update && sudo apt install -y make build-essential libssl-dev \
  zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
  libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
#    Fedora/RHEL:
# sudo dnf install -y make gcc zlib-devel bzip2 bzip2-devel readline-devel \
#   sqlite sqlite-devel openssl-devel tk-devel libffi-devel xz-devel

# 5. Install Python 3.12 and create venv
pyenv install 3.12
pyenv local 3.12
python -m venv .venv
source .venv/bin/activate

# 6. Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 7. Create .env with your bot token
cp .env.example .env
nano .env   # paste your DISCORD_TOKEN

# 8. Run tests
pytest -v

# 9. Run the bot
cd src
python -m bot
```

### No sudo? Skip pyenv entirely

If Python 3.12+ is already installed on your system:

```bash
# Check what's available
python3 --version
python3.12 --version

# If 3.12+ exists, skip pyenv and go straight to:
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

---

## Verification Checklist

After setup, verify everything works:

- [ ] `python --version` → Python 3.12.x
- [ ] `which python` → points to `.venv/bin/python`
- [ ] `pip list | grep discord` → discord.py installed
- [ ] `pytest -v` → all tests pass
- [ ] `ruff check src/ tests/` → no lint errors
- [ ] Bot comes online in Discord when you run `cd src && python -m bot`
- [ ] `/hello` command responds with "Hello, World! 🎲"

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `pyenv: command not found` | Restart your terminal or re-source your shell config |
| `ModuleNotFoundError: No module named '_lzma'` | Install `xz` (macOS: `brew install xz`) or `liblzma-dev` (Linux) then reinstall Python: `pyenv uninstall 3.12.x && pyenv install 3.12` |
| `Cannot connect to host discord.com` | Network/firewall is blocking Discord — try a different network |
| `/hello` doesn't appear in Discord | Slash commands can take up to 1 hour to sync globally. Wait and retry |
| `RuntimeError: DISCORD_TOKEN is not set` | Make sure `.env` exists in the project root with `DISCORD_TOKEN=your-token` |

