.PHONY: help install install-dev format lint type-check test test-cov clean run docker-build docker-run

help:
	@echo "Verfügbare Befehle:"
	@echo "  make install      Produktions-Abhängigkeiten installieren"
	@echo "  make install-dev  Entwicklungs-Abhängigkeiten installieren"
	@echo "  make format       Code mit black und ruff formatieren"
	@echo "  make lint         Linting-Prüfungen durchführen"
	@echo "  make type-check   Type-Checking mit mypy durchführen"
	@echo "  make test         Tests ausführen"
	@echo "  make test-cov     Tests mit Coverage ausführen"
	@echo "  make clean        Generierte Dateien bereinigen"
	@echo "  make run          Anwendung starten"
	@echo "  make docker-build Docker-Image erstellen"
	@echo "  make docker-run   Docker-Container ausführen"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pre-commit install

format:
	black src/ tests/
	ruff check --fix src/ tests/
	isort src/ tests/

lint:
	ruff check src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/
	flake8 src/ tests/

type-check:
	mypy src/

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf build/ dist/ *.egg-info
	rm -rf htmlcov/ .coverage

run:
	python run.py

docker-build:
	docker build -t mine-search:latest .

docker-run:
	docker-compose up -d

pre-commit-all:
	pre-commit run --all-files