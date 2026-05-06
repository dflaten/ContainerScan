# ContainerScan

ContainerScan is a LAN-only web app for labeling storage containers with QR codes and browsing their contents.

## Development Setup

The repository now includes a development compose override with:

- bind mounts for `backend/` and `frontend/`
- backend auto-reload via `uvicorn --reload`
- frontend dev server via `vite`
- direct access to Postgres, backend, frontend, and Nginx

### Prerequisites

- Docker Engine with the Compose plugin

### Start The Dev Stack

Run from the repository root:

```bash
make dev-build
```

Available endpoints:

- App via Nginx: `http://localhost`
- Frontend dev server: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Postgres: `localhost:5432`

### Stop The Dev Stack

```bash
make dev-down
```

To also remove the database volume:

```bash
make dev-reset
```

## Database Migrations

Start the stack first so Postgres is available, then run migrations in the backend container:

```bash
make migrate
```

Check the current migration version:

```bash
make migrate-status
```

Generate a new revision after model changes:

```bash
make migrate-revision MSG="describe change"
```

## Useful Local Commands

Backend lint:

```bash
make backend-lint
```

Backend type/import sanity:

```bash
make backend-compile
```

Frontend production build:

```bash
make frontend-build
```
