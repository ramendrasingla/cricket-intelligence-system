.PHONY: install test lint format clean help pipeline-stats pipeline-news agent

help:
	@echo "Cricket Intelligence System - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install package in development mode"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-cov         Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linters (ruff, mypy)"
	@echo "  make format           Format code (black, ruff)"
	@echo ""
	@echo "Pipelines:"
	@echo "  make pipeline-stats   Run cricket stats pipeline"
	@echo "  make pipeline-news    Run news ingestion pipeline"
	@echo ""
	@echo "Agent:"
	@echo "  make agent            Run cricket intelligence agent CLI"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove build artifacts and caches"

install:
	pip install -e ".[dev]"

test:
	pytest

test-unit:
	pytest -m unit

test-integration:
	pytest -m integration

test-cov:
	pytest --cov=src/cricket_intelligence --cov-report=html --cov-report=term

lint:
	ruff check src/ tests/
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/
	ruff check --fix src/ tests/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

pipeline-stats:
	python -m cricket_intelligence.pipelines.stats.ingest_bronze
	python -m cricket_intelligence.pipelines.stats.transform_silver

pipeline-news:
	python -m cricket_intelligence.pipelines.news.ingest

agent:
	python -m cricket_intelligence.agent.cli
