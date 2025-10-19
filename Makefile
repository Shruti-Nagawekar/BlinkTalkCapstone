# BlinkTalk Backend Makefile

.PHONY: help setup install run test fmt lint clean

# Default target
help:
	@echo "BlinkTalk Backend Commands:"
	@echo "  setup     - Install dependencies and setup environment"
	@echo "  install   - Install package in development mode"
	@echo "  run       - Start the FastAPI server"
	@echo "  test      - Run tests"
	@echo "  fmt       - Format code with black and isort"
	@echo "  lint      - Run linting with ruff"
	@echo "  clean     - Clean up build artifacts"

# Setup environment
setup:
	@echo "Setting up BlinkTalk backend..."
	cd py && python -m pip install --upgrade pip
	cd py && pip install -e ".[dev]"
	@echo "Setup complete!"

# Install package
install:
	cd py && pip install -e .

# Run the server
run:
	@echo "Starting BlinkTalk API server on http://localhost:8011"
	cd py && python -m uvicorn api.main:app --host 0.0.0.0 --port 8011 --reload

# Run tests
test:
	@echo "Running tests..."
	cd py && python -m pytest

# Format code
fmt:
	@echo "Formatting code..."
	cd py && black .
	cd py && isort .

# Run linting
lint:
	@echo "Running linters..."
	cd py && ruff check .
	cd py && mypy .

# Clean up
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

