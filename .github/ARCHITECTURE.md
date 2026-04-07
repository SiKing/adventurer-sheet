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

## ADR-008 — Git Workflow Rules

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

## ADR-009 — Dependency Review at Plan Completion

**Date:** 2026-04-07

### Rule

When all steps of a Plan have been completed and tests are passing, **check for
newer versions of every package in `requirements.txt` and `requirements-dev.txt`**
before merging the branch. Update packages that have safe upgrades available;
document any that are intentionally held back.

### Rationale

Feature branches take time. A package that was current at the start of a plan
may have received bug fixes, security patches, or compatible minor releases by
the time the branch is ready to merge. Reviewing at plan completion — rather than
on an ad-hoc schedule — creates a consistent, low-effort cadence that keeps
dependencies fresh without disrupting active development.

The alternative (never reviewing until something breaks) leads to large, risky
upgrade batches and missed security patches.

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

If a package is intentionally held back, document it inline:

```
# discord.py~=2.4  # held at 2.x — 3.0 has breaking slash-command API changes
discord.py~=2.4
```

### What "safe upgrade" means

- **`requirements-dev.txt`:** Any new version is worth testing. These packages
  do not ship to production; the only risk is a lint rule change or a test
  runner behavioural difference — both of which are caught immediately by CI.
- **`requirements.txt`:** Patch and minor upgrades within the `~=` range are
  safe by definition (semantic versioning). Major upgrades require a changelog
  review and dedicated branch.

### Example: Phase 2 lesson

`ruff` was unpinned in `requirements-dev.txt`. CI installed a newer version that
flagged an import-sorting error that the local version silently accepted. The fix
was to pin `ruff==0.15.9`. A dependency review at Phase 2 completion would have
caught this proactively — either by upgrading local ruff to match CI, or by
pinning CI to match local, before the discrepancy caused a CI failure.

---

