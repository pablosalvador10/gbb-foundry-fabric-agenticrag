# =============================================================================
# GBB Foundry Fabric AgenticRAG - Makefile
# =============================================================================

# Configuration
PYTHON := python
CONDA_ENV := gbb-foundry-agenticrag
APP_NAME := airline-ops-assistant
DOCKER_IMAGE := $(APP_NAME)
DOCKER_TAG := latest
PORT := 8501

# Export PYTHONPATH for module resolution
export PYTHONPATH := $(PWD):$(PYTHONPATH)

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m

.PHONY: help install run dev test lint format clean docker-build docker-run docker-up docker-down create-agent

# Default target
help:
	@echo "$(GREEN)Available targets:$(NC)"
	@echo ""
	@echo "  $(YELLOW)Development:$(NC)"
	@echo "    install        - Create conda environment and install dependencies"
	@echo "    run            - Run the Streamlit application"
	@echo "    dev            - Run app in development mode with auto-reload"
	@echo "    create-agent   - Create RealtimeAssistant with file search (run once)"
	@echo ""
	@echo "  $(YELLOW)Code Quality:$(NC)"
	@echo "    lint           - Run linting checks (ruff)"
	@echo "    format         - Format code (black, isort)"
	@echo "    test           - Run unit tests"
	@echo ""
	@echo "  $(YELLOW)Docker:$(NC)"
	@echo "    docker-build   - Build Docker image"
	@echo "    docker-run     - Run Docker container"
	@echo "    docker-up      - Start with docker-compose"
	@echo "    docker-down    - Stop docker-compose services"
	@echo ""
	@echo "  $(YELLOW)Cleanup:$(NC)"
	@echo "    clean          - Remove cache files and build artifacts"

# =============================================================================
# Development
# =============================================================================

install:
	@echo "$(GREEN)Creating conda environment...$(NC)"
	conda env create -f environment.yaml || conda env update -f environment.yaml
	@echo "$(GREEN)Done! Activate with: conda activate $(CONDA_ENV)$(NC)"

run:
	@echo "$(GREEN)Starting Airline Operations Assistant...$(NC)"
	streamlit run app/main.py --server.port $(PORT)

dev:
	@echo "$(GREEN)Starting in development mode...$(NC)"
	streamlit run app/main.py --server.port $(PORT) --server.runOnSave true

create-agent:
	@echo "$(GREEN)Creating RealtimeAssistant agent with file search capability...$(NC)"
	@echo "This will upload airport_operations.pdf and create a vector store in Azure AI Foundry"
	@echo ""
	$(PYTHON) -m app.agent_registry.RealtimeAssistant.create_agent
	@echo ""
	@echo "$(GREEN)Done! Copy the printed IDs and add them to your .env file$(NC)"

# =============================================================================
# Code Quality
# =============================================================================

lint:
	@echo "$(GREEN)Running linting checks...$(NC)"
	$(PYTHON) -m ruff check app/ src/ utils/

format:
	@echo "$(GREEN)Formatting code...$(NC)"
	$(PYTHON) -m black app/ src/ utils/
	$(PYTHON) -m isort app/ src/ utils/
	$(PYTHON) -m ruff check app/ src/ utils/ --fix

test:
	@echo "$(GREEN)Running tests...$(NC)"
	$(PYTHON) -m pytest tests/ -v --cov=app --cov-report=term-missing

# =============================================================================
# Docker
# =============================================================================

docker-build:
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) -f app/Dockerfile .

docker-run:
	@echo "$(GREEN)Running Docker container...$(NC)"
	docker run --rm -p $(PORT):$(PORT) --env-file .env $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-up:
	@echo "$(GREEN)Starting services with docker-compose...$(NC)"
	docker-compose -f app/docker-compose.yaml up -d

docker-down:
	@echo "$(GREEN)Stopping docker-compose services...$(NC)"
	docker-compose -f app/docker-compose.yaml down

docker-logs:
	docker-compose -f app/docker-compose.yaml logs -f

# =============================================================================
# Conda Environment Management
# =============================================================================

conda-create:
	conda env create -f environment.yaml

conda-update:
	conda env update -f environment.yaml --prune

conda-remove:
	conda env remove --name $(CONDA_ENV)

# =============================================================================
# Cleanup
# =============================================================================

clean:
	@echo "$(GREEN)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "$(GREEN)Done!$(NC)"
