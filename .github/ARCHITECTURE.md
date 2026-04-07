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

