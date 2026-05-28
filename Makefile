.PHONY: setup dev test lint format

setup:
	python -m pip install -U pip
	pip install -e ".[dev]"
	python -m playwright install chromium || true

dev:
	uvicorn leadradar.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -q

lint:
	ruff check src tests
	mypy src || true

format:
	ruff format src tests
	ruff check --fix src tests
