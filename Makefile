.PHONY: up down logs migrate shell-api test seed

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec api alembic upgrade head

shell-api:
	docker compose exec api bash

test:
	docker compose exec api pytest

seed:
	docker compose exec api python -m app.scripts.seed
