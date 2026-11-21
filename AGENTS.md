# Agent Notes

ContainerScan is a LAN-only web app for labeling storage containers with QR
codes. The backend is FastAPI + SQLAlchemy managed with `uv`; the frontend is
SvelteKit managed with `npm`. The root `Makefile` is the canonical entry point
for developer commands.

## Layout

- `backend/` - FastAPI app, models, migrations, and tests (`uv`, `pytest`)
- `frontend/` - SvelteKit app and tests (`npm`, `vitest`)
- `deploy/` - Nginx configuration
- `docker-compose.yml` - production stack
- `docker-compose.dev.yml` - development overrides

## Common Commands

```bash
make help              # list all targets
make dev-build         # start the development stack
make dev-down          # stop the development stack
make migrate           # apply database migrations
make backend-lint      # ruff checks
make backend-test      # backend tests
make frontend-test     # frontend tests (single run)
make frontend-build    # frontend production build
make test              # backend and frontend tests
```

Run commands through `make` when a target exists. Do not add ad-hoc package
manager invocations that duplicate a Makefile target.

## Updating Dependencies

Preview available updates without modifying anything:

```bash
make deps-outdated
```

Update dependencies:

```bash
make update-deps
```

- Backend: runs `uv lock --upgrade` and `uv sync`. Versions are limited by the
  ranges in `backend/pyproject.toml`.
- Frontend: runs `npm-check-updates --target minor -u` and `npm install`, so
  major versions are not crossed.

To allow frontend major version bumps:

```bash
make update-deps-major
```

Backend majors still require manually widening the ranges in
`backend/pyproject.toml`. Major updates can require code changes; after either
update command, always verify and review:

```bash
make test
make frontend-build
git diff
```

Commit both `backend/uv.lock` and `frontend/package-lock.json` with any
dependency changes. If `npm install` fails after `npm-check-updates` rewrites
`package.json`, there is no automatic rollback. Reset the frontend manifests and
retry:

```bash
git checkout -- frontend/package.json frontend/package-lock.json
```

Docker image tags (`postgres`, `nginx`, `python`, `node`) and the pinned `uv`
image in `backend/Dockerfile` are managed manually and are not updated by these
targets.

`npm-check-updates` is pinned in the Makefile via `NCU_VERSION`. Override it only
when you intentionally want a different tool version:

```bash
make update-deps NCU_VERSION=latest
```
