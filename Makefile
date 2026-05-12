COMPOSE := docker compose -f docker-compose.yml -f docker-compose.dev.yml

.PHONY: help dev-up dev-build dev-down dev-reset logs ps migrate migrate-status migrate-revision seed-dev backend-lint backend-compile backend-test frontend-build frontend-test test

help:
	@printf '%s\n' \
		'Available targets:' \
		'  make dev-up            Start the development stack' \
		'  make dev-build         Rebuild and start the development stack' \
		'  make dev-down          Stop the development stack' \
		'  make dev-reset         Stop the stack and remove volumes' \
		'  make logs              Tail logs from all services' \
		'  make ps                Show service status' \
		'  make migrate           Apply database migrations' \
		'  make migrate-status    Show the current migration version' \
		'  make migrate-revision MSG="name"  Create a new migration revision' \
		'  make seed-dev          Seed the development database with sample records' \
		'  make backend-lint      Run backend lint checks' \
		'  make backend-compile   Run backend import/compile checks' \
		'  make backend-test      Run backend tests' \
		'  make frontend-build    Run the frontend production build' \
		'  make frontend-test     Run frontend tests' \
		'  make test              Run backend and frontend tests'

dev-up:
	$(COMPOSE) up

dev-build:
	$(COMPOSE) up --build

dev-down:
	$(COMPOSE) down

dev-reset:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

migrate:
	$(COMPOSE) exec backend uv run alembic upgrade head

migrate-status:
	$(COMPOSE) exec backend uv run alembic current

migrate-revision:
	@test -n "$(MSG)" || (echo 'Usage: make migrate-revision MSG="describe change"' && exit 1)
	$(COMPOSE) exec backend uv run alembic revision -m "$(MSG)"

seed-dev:
	$(COMPOSE) exec backend uv run python scripts/seed_dev_data.py

backend-lint:
	cd backend && ./.venv/bin/ruff check .

backend-compile:
	cd backend && ./.venv/bin/python -m py_compile main.py config.py database.py models.py alembic/env.py

backend-test:
	cd backend && uv run pytest

frontend-build:
	cd frontend && npm run build

frontend-test:
	cd frontend && npm test

test: backend-test frontend-test
