# Detect OS
ifeq ($(OS),Windows_NT)
    VENV_BIN = venv/Scripts
    PYTHON_BIN = $(VENV_BIN)/python.exe
    PIP_BIN = $(VENV_BIN)/pip.exe
    UVICORN_BIN = $(VENV_BIN)/uvicorn.exe
    PYTEST_BIN = $(VENV_BIN)/pytest.exe
    BLACK_BIN = $(VENV_BIN)/black.exe
    FLAKE8_BIN = $(VENV_BIN)/flake8.exe
    MYPY_BIN = $(VENV_BIN)/mypy.exe
    ISORT_BIN = $(VENV_BIN)/isort.exe
    CELERY_BIN = $(VENV_BIN)/celery.exe
else
    VENV_BIN = venv/bin
    PYTHON_BIN = $(VENV_BIN)/python
    PIP_BIN = $(VENV_BIN)/pip
    UVICORN_BIN = $(VENV_BIN)/uvicorn
    PYTEST_BIN = $(VENV_BIN)/pytest
    BLACK_BIN = $(VENV_BIN)/black
    FLAKE8_BIN = $(VENV_BIN)/flake8
    MYPY_BIN = $(VENV_BIN)/mypy
    ISORT_BIN = $(VENV_BIN)/isort
    CELERY_BIN = $(VENV_BIN)/celery
endif

.PHONY: install run run-worker test lint format clean

install:
	python -m venv venv
	$(PIP_BIN) install --upgrade pip
	$(PIP_BIN) install -r requirements.txt

run:
	$(UVICORN_BIN) app.main:app --reload --host 127.0.0.1 --port 8000

run-worker:
	$(CELERY_BIN) -A app.core.celery_app worker --loglevel=info

test:
	$(PYTEST_BIN)

lint:
	$(FLAKE8_BIN) app tests
	$(MYPY_BIN) app

format:
	$(BLACK_BIN) app tests
	$(ISORT_BIN) app tests

clean:
	rm -rf venv
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache
