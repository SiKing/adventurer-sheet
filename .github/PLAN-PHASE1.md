# Phase 1 Plan — Hello World Full Pipeline

> **Goal:** A trivial Discord bot with a `/hello` slash command, fully deployed through  
> code → GitHub → CI/CD → Railway → live in Discord.

---

## Step 1: Local Environment Setup

**⏱ ~15 minutes**

### 1.1 Install pyenv via Homebrew

```bash
brew install pyenv
```

### 1.2 Configure your shell for pyenv

Add these lines to your `~/.bash_profile` (or `~/.zshrc` if using zsh):

```bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

Then reload your shell:

```bash
source ~/.bash_profile    # or: source ~/.zshrc
```

### 1.3 Install Python 3.12

```bash
pyenv install 3.12
```

### 1.4 Set Python 3.12 for this project

```bash
cd /Users/marklehky/PycharmProjects/PythonProject
pyenv local 3.12
```

This creates a `.python-version` file. Verify:

```bash
python --version
# Should output: Python 3.12.x
```

### 1.5 Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 1.6 Install dependencies

```bash
pip install discord.py python-dotenv
pip install --dev ruff pytest pytest-cov pytest-asyncio
```

Or, after we create `requirements.txt` in Step 3:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### ✅ Verification

- [ ] `python --version` shows 3.12.x
- [ ] `which python` points to `.venv/bin/python`
- [ ] `pip list` shows discord.py, python-dotenv

---

## Step 2: Discord Application Setup

**⏱ ~10 minutes**

### 2.1 Create a Discord Application

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Name it **"Adventurer Sheet"**
4. Click **Create**

### 2.2 Create the Bot user

1. In the left sidebar, click **"Bot"**
2. Click **"Reset Token"** and confirm
3. **Copy the token immediately** — you won't see it again
4. Under **Privileged Gateway Intents**, enable **Message Content Intent**
5. Click **Save Changes**

> ⚠️ **NEVER commit this token to git.** It goes in `.env` only.

### 2.3 Store the token locally

Create a `.env` file in the project root:

```bash
DISCORD_TOKEN=paste-your-token-here
```

### 2.4 Generate the invite URL

1. In the left sidebar, click **"OAuth2"**
2. Under **OAuth2 URL Generator**, check these scopes:
   - `bot`
   - `applications.commands`
3. Under **Bot Permissions**, check:
   - `Send Messages`
   - `Use Slash Commands`
4. Copy the generated URL at the bottom

### 2.5 Invite the bot to your test server

1. Paste the URL in your browser
2. Select your test server from the dropdown
3. Click **Authorize**
4. The bot should now appear in your server's member list (offline)

### ✅ Verification

- [ ] Bot token saved in `.env`
- [ ] Bot appears in test server member list (offline is fine)

---

## Step 3: Project Structure & Hello World Bot

**⏱ ~20 minutes**

### 3.1 Target directory structure

```
adventurer-sheet/
├── .env                  # Secret bot token (NEVER committed)
├── .env.example          # Template showing required env vars
├── .github/
│   ├── IDEAS.md          # Project vision and decisions
│   ├── PLAN-PHASE1.md    # This file
│   └── workflows/
│       └── ci.yml        # GitHub Actions pipeline
├── .gitignore
├── .python-version       # pyenv: 3.12
├── Dockerfile            # For Railway deployment
├── Procfile              # Railway start command
├── README.md
├── pyproject.toml        # Project metadata and tool config
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Dev/test dependencies
├── src/
│   └── bot/
│       ├── __init__.py
│       ├── __main__.py   # Entry point: python -m bot
│       ├── config.py     # Loads env vars safely
│       └── cogs/
│           ├── __init__.py
│           └── hello.py  # /hello slash command
└── tests/
    ├── __init__.py
    └── test_config.py    # Verify config loading
```

**Why this structure:**
- `src/bot/` keeps source code isolated — standard Python packaging pattern
- `cogs/` is discord.py's extension pattern — each feature gets its own file (Phase 2 will add character sheet cogs)
- `tests/` is separate from source — pytest convention
- `__main__.py` allows running with `python -m bot` from `src/`

### 3.2 Files to create

All files will be created in the implementation step. Here's what each one does:

| File | Purpose |
|------|---------|
| `src/bot/__main__.py` | Creates the bot, loads cogs, connects to Discord |
| `src/bot/config.py` | Reads `.env`, validates that `DISCORD_TOKEN` is set, fails fast if missing |
| `src/bot/cogs/hello.py` | A Cog with a `/hello` slash command returning "Hello, World! 🎲" |
| `.env.example` | Template: `DISCORD_TOKEN=your-token-here` |
| `.gitignore` | Python, .env, SQLite, IDE, venv ignores |
| `Dockerfile` | Multi-stage build for Railway |
| `Procfile` | `worker: python -m bot` (tells Railway this is not a web server) |
| `pyproject.toml` | Project name, version, Python requirement, ruff/pytest config |
| `requirements.txt` | `discord.py~=2.4` and `python-dotenv~=1.0` |
| `requirements-dev.txt` | `ruff`, `pytest`, `pytest-cov`, `pytest-asyncio` |
| `README.md` | Project description, setup instructions, how to run |
| `tests/test_config.py` | Verifies config loads correctly, fails on missing token |

### ✅ Verification

- [ ] All files created
- [ ] `ruff check src/` passes with no errors
- [ ] `pytest` passes

---

## Step 4: Local Testing

**⏱ ~5 minutes**

### 4.1 Run the bot

```bash
cd /Users/marklehky/PycharmProjects/PythonProject
source .venv/bin/activate
cd src
python -m bot
```

You should see console output like:

```
Logged in as Adventurer Sheet#1234
Syncing commands...
Commands synced. Bot is ready.
```

### 4.2 Test in Discord

1. Open Discord and go to your test server
2. The bot should show as **online** (green dot)
3. Type `/hello` in any channel — Discord's autocomplete should show the command
4. Press Enter
5. Bot responds: **"Hello, World! 🎲"**

### 4.3 Stop the bot

Press `Ctrl+C` in the terminal. The bot should go offline in Discord.

### ✅ Verification

- [ ] Bot comes online when script runs
- [ ] `/hello` command appears in Discord's autocomplete
- [ ] Bot responds with "Hello, World! 🎲"
- [ ] Bot goes offline when script is stopped

---

## Step 5: GitHub Repository Setup

**⏱ ~10 minutes**

### 5.1 Initialize and commit

```bash
cd /Users/marklehky/PycharmProjects/PythonProject
git init
git add .
git commit -m "feat: add hello-world discord bot with CI/CD scaffold"
```

### 5.2 Create the GitHub repo

**Option A — GitHub CLI (if installed):**

```bash
gh repo create adventurer-sheet --public --source=. --remote=origin --push
```

**Option B — Manual:**

1. Go to [github.com/new](https://github.com/new)
2. Name: `adventurer-sheet`
3. Do **not** initialize with README (we already have one)
4. Create the repo
5. Then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/adventurer-sheet.git
git branch -M main
git push -u origin main
```

### ✅ Verification

- [ ] Code visible on GitHub
- [ ] `.env` is **not** in the repo (check!)
- [ ] `.env.example` **is** in the repo

---

## Step 6: Railway.app Deployment

**⏱ ~15 minutes**

### 6.1 Create a Railway account

1. Go to [railway.app](https://railway.app)
2. Sign up with your GitHub account (simplest — auto-links repos)

### 6.2 Create a new project

1. Click **"New Project"**
2. Choose **"Deploy from GitHub Repo"**
3. Select `adventurer-sheet`
4. Railway will auto-detect the Dockerfile

### 6.3 Configure environment variables

1. In your Railway project, go to the service **Variables** tab
2. Add: `DISCORD_TOKEN` = (paste your bot token)

### 6.4 Configure as a worker (not a web server)

The `Procfile` tells Railway to use `worker: python -m bot`. Verify in Railway's settings that:
- It is **not** trying to assign a public domain/port
- The service type is recognized as a worker process

> ⚠️ **Common pitfall:** Railway may try to health-check a web port and restart your bot.
> The `Procfile` with `worker:` prefix prevents this. If you still see restarts, go to
> Settings → Networking and remove any port/domain assignment.

### 6.5 Deploy

Railway will auto-deploy on push. For the first time, you can trigger it manually from the Railway dashboard.

### 6.6 Verify

1. Check Railway logs — should show "Logged in as Adventurer Sheet#1234"
2. Check Discord — bot should be online
3. Run `/hello` — should respond

### ✅ Verification

- [ ] Railway deployment succeeds (green in dashboard)
- [ ] Railway logs show bot connected
- [ ] Bot is online in Discord
- [ ] `/hello` works

> 📝 **Note on Railway free tier:** The free trial gives you $5 credit. After that, the
> Hobby plan is $5/month. A Discord bot (always-on WebSocket) will use the free credit
> in ~2-3 weeks. Plan to upgrade to Hobby if you want 24/7 uptime.

---

## Step 7: GitHub Actions CI/CD Pipeline

**⏱ ~15 minutes**

### 7.1 Get your Railway deploy token

1. In Railway, go to your project → **Settings** → **Tokens**
2. Create a new project token
3. Copy it

### 7.2 Store secrets in GitHub

1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Add secret: `RAILWAY_TOKEN` = (paste the Railway token)

### 7.3 Create the workflow file

File: `.github/workflows/ci.yml`

The pipeline will:
1. **On every push/PR:** Lint with ruff → Run tests with pytest
2. **On push to `main` only:** Deploy to Railway

See the file in Step 3's directory structure — it will be created during implementation.

### 7.4 Verify the pipeline

Push any small change:

```bash
git add .
git commit -m "ci: add GitHub Actions workflow"
git push
```

Check the **Actions** tab on GitHub — the workflow should run and pass.

### ✅ Verification

- [ ] GitHub Actions workflow runs on push
- [ ] Lint step passes
- [ ] Test step passes
- [ ] Deploy step triggers on `main` push
- [ ] Railway redeploys after GitHub Actions deploy

---

## Step 8: End-to-End Verification

**⏱ ~5 minutes**

### 8.1 Make a visible change

Change the `/hello` response text to something different, e.g., "Greetings, adventurer! 🎲⚔️"

### 8.2 Push through the full pipeline

```bash
git add .
git commit -m "feat: update hello command response"
git push
```

### 8.3 Watch the pipeline

1. GitHub Actions: lint ✅ → test ✅ → deploy ✅
2. Railway: redeploys automatically
3. Discord: `/hello` now shows the updated message

### ✅ Final Verification

- [ ] Code pushed to GitHub
- [ ] GitHub Actions pipeline passed (all steps green)
- [ ] Railway redeployed automatically
- [ ] Bot responds with updated message in Discord
- [ ] Full pipeline works: **code → push → CI → deploy → live in Discord** ✅

---

## Summary of Accounts Needed

| Service | URL | Purpose | Cost |
|---------|-----|---------|------|
| **GitHub** | github.com | Code hosting, CI/CD | Free |
| **Discord Developer** | discord.com/developers | Bot application & token | Free |
| **Railway** | railway.app | Production hosting | Free trial ($5), then $5/mo Hobby |

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| Bot token leaked to git | `.gitignore` excludes `.env`; `.env.example` has no real values |
| Railway free tier runs out | Monitor usage; upgrade to Hobby ($5/mo) when ready |
| Slash commands don't appear | Commands need to sync — may take up to 1 hour for global sync; use guild sync for instant dev updates |
| Railway health-check kills bot | `Procfile` uses `worker:` prefix; remove port assignment in Railway settings |
| pyenv conflicts with system Python | `.python-version` file pins version per-project; system Python unaffected |

---

## What's Next (Phase 2 Preview)

Phase 2 will build on this foundation to add:
- SQLite database via SQLAlchemy for character sheet storage
- Character CRUD commands (create, view, edit, delete)
- Discord user ID-based ownership/security
- Embedded rich messages for character sheet display

