# Python settings
PYTHON := python3
VENV := venv
BIN := $(VENV)/bin
PYTHON_VENV := $(BIN)/python
PIP := $(BIN)/pip

# Application settings
APP_MODULE := app.main:app
HOST := 0.0.0.0
PORT := 8000

# Main commands
.PHONY: all setup clean install run dev lint format help

all: help

help:
	@echo "Available commands:"
	@echo "setup      - Create virtual environment and install dependencies"
	@echo "clean      - Remove Python artifacts and virtualenv"
	@echo "install    - Install project dependencies"
	@echo "run        - Run the application in production mode"
	@echo "dev        - Run the application in development mode"
	@echo "lint       - Check code style"
	@echo "format     - Format code"

# Environment setup
$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip

setup: $(VENV)/bin/activate install

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

install:
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

# Development commands
dev:
	$(BIN)/uvicorn $(APP_MODULE) --reload --host $(HOST) --port $(PORT)

run:
	$(BIN)/uvicorn $(APP_MODULE) --host $(HOST) --port $(PORT)

# Code quality
lint:
	$(BIN)/flake8 app subtitle_service_base.py
	$(BIN)/mypy app subtitle_service_base.py

format:
	$(BIN)/black app subtitle_service_base.py
	$(BIN)/isort app subtitle_service_base.py

# Install development dependencies
install-dev:
	$(PIP) install -r requirements-dev.in

# Update dependencies
update-deps:
	$(PIP) install --upgrade -r requirements.txt