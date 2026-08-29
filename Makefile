.PHONY: setup build migrate sync search test lint down

setup:
	cp .env.example .env

build:
	docker compose build

migrate:
	docker compose --profile tools run --rm migrate

sync:
	docker compose --profile tools run --rm cli sync --full

search:
	docker compose --profile tools run --rm cli search "$(Q)"

test:
	docker build --target test -t confluence-knowledge-poc:test .
	docker run --rm confluence-knowledge-poc:test

lint:
	python -m ruff check src tests

down:
	docker compose down
