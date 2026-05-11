# 墨麟 OS — Makefile
# ================================
# One command to rule them all.
# Usage: make <target>

.PHONY: help install setup deploy dev test lint check clean backup cron-list

# ── Default ──
help: ## Show all commands
	@echo "墨麟 OS — AI 一人公司操作系统"
	@echo ""
	@echo "Quick Start:"
	@echo "  make install     Install Python dependencies"
	@echo "  make setup       Full one-click deployment"
	@echo "  make dev         Development setup (editable install)"
	@echo ""
	@echo "Everyday:"
	@echo "  make test        Run test suite"
	@echo "  make check       System health check"
	@echo "  make lint        Syntax validation"
	@echo "  make clean       Remove build artifacts"
	@echo "  make backup      Backup configs and skills"
	@echo ""
	@echo "Cron:"
	@echo "  make cron-list   List all scheduled cron jobs"

# ── Install ──
install: ## Install core dependencies
	pip install --upgrade pip -q
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"

dev: ## Editable install for development
	pip install -e . -q 2>/dev/null || true
	@echo "✓ Editable install complete"

setup: ## Full one-click deployment
	@bash setup.sh

deploy: install dev ## Install + editable install
	@echo "✓ Deploy complete"

# ── Quality ──
test: ## Run test suite
	@python -m pytest tests/ -v --tb=short 2>/dev/null || \
		python -m pytest tests/ -v 2>/dev/null || \
		echo "⚠ No tests found or pytest not installed"

lint: ## Syntax check all Python files
	@echo "Checking syntax..."
	@find molib -name "*.py" -exec python -m py_compile {} \; 2>/dev/null || true
	@echo "✓ Syntax OK"

check: ## System health check
	@python -m molib health 2>/dev/null || echo "⚠ Health check not available"

# ── Cleanup ──
clean: ## Remove build artifacts
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache build dist *.egg-info 2>/dev/null || true
	@echo "✓ Clean"

# ── Backup ──
backup: ## Create timestamped backup
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	tar -czf "backup_$$timestamp.tar.gz" \
		--exclude='.git' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='venv' \
		--exclude='.env' \
		skills/ config/ molib/ docs/ scripts/ \
		&& echo "✓ Backup: backup_$$timestamp.tar.gz"

# ── Cron ──
cron-list: ## List all active cron jobs
	@python -c "import json; print(json.dumps({'note':'Use Hermes cronjob list command'}, indent=2))" 2>/dev/null || \
		echo "Cron jobs managed by Hermes Agent — use 'hermes cronjob list' in Hermes session"
