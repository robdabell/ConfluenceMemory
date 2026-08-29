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
	docker build --target runtime -t confluence-knowledge-poc:test .
	docker run --rm --entrypoint sh confluence-knowledge-poc:test -c "pip install '.[dev]' && pytest"

lint:
	python -m ruff check src tests

down:
	docker compose down

