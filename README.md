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

## Server Deployment

Use the repository's own `docker-compose.yml` for deployment. Do not use `docker-compose.dev.yml` on the server.

Copy the sample env file:

```bash
cp .env.example .env
```

Set at least:

- `CONTAINERSCAN_HTTP_PORT`
- `CONTAINERSCAN_PUBLIC_BASE_URL`
- `CONTAINERSCAN_DB_DATA_LOCATION`
- `CONTAINERSCAN_IMAGE_DATA_LOCATION`
- `CONTAINERSCAN_DB_NAME`
- `CONTAINERSCAN_DB_USER`
- `CONTAINERSCAN_DB_PASSWORD`

Create the persistent directories before first start:

```bash
sudo mkdir -p /srv/containerscan/postgres /srv/containerscan/images
sudo chown -R 1000:1000 /srv/containerscan/images
```

Then start the stack:

```bash
docker compose up -d --build
```

Important deployment notes:

- `CONTAINERSCAN_PUBLIC_BASE_URL` must match the durable LAN URL you want printed into QR codes.
- If you change the hostname or port later, old QR labels will still point at the old address.
- The backend runs `alembic upgrade head` automatically during container startup.
- The default sample port is `8088`, which avoids assuming host port `80` is free.

## Database Migrations

Start the stack first so Postgres is available, then run migrations in the backend container:

```bash
make migrate
```

Check the current migration version:

```bash
make migrate-status
```

Seed the development database with sample rooms, labels, and containers:

```bash
make seed-dev
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
