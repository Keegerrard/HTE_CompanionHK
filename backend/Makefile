.PHONY: install dev test lint uv-sync uv-dev uv-test uv-lint conda-create conda-dev conda-test conda-lint

install:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -e '.[dev]'

dev:
	. .venv/bin/activate && uvicorn app.main:app --reload --port 8000

test:
	. .venv/bin/activate && pytest -q

lint:
	. .venv/bin/activate && ruff check app tests

uv-sync:
	uv sync --all-extras

uv-dev:
	uv run uvicorn app.main:app --reload --port 8000

uv-test:
	uv run pytest -q

uv-lint:
	uv run ruff check app tests

conda-create:
	conda env create -f environment.yml || conda env update -f environment.yml --prune

conda-dev:
	conda run -n companionhk-backend uvicorn app.main:app --reload --port 8000

conda-test:
	conda run -n companionhk-backend pytest -q

conda-lint:
	conda run -n companionhk-backend ruff check app tests
