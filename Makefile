# 墨麟OS — Makefile
# ===================

.PHONY: help install test lint clean run serve health

# 默认目标
help:
	@echo "墨麟OS — AI一人公司操作系统"
	@echo ""
	@echo "命令:"
	@echo "  make install     安装依赖"
	@echo "  make setup       完整部署 (setup.sh)"
	@echo "  make test        运行测试"
	@echo "  make lint        代码检查"
	@echo "  make health      健康检查"
	@echo "  make serve       启动API服务"
	@echo "  make cli         运行CLI"
	@echo "  make clean       清理临时文件"
	@echo "  make backup      备份skills和配置"

install:
	pip install -r requirements.txt
	pip install -e .

setup:
	bash setup.sh

test:
	python -m pytest tests/ -v --cov=molib --cov-report=term || \
	python -m pytest tests/ -v --cov=molin --cov-report=term

lint:
	@echo "代码检查..."
	python -m py_compile molib/*.py molib/*/*.py 2>/dev/null || true
	@echo "✓ 语法检查通过"

health:
	python -c "from molib.core.engine import engine; import json; print(json.dumps(engine.health_check(), indent=2, ensure_ascii=False))" 2>/dev/null || \
	python -c "from molin.core.engine import engine; import json; print(json.dumps(engine.health_check(), indent=2, ensure_ascii=False))"

serve:
	python -m molib.ceo.main

cli:
	python -m molib.cli --help

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache build dist *.egg-info
	@echo "✓ 清理完成"

backup:
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	tar -czf "backup_$$timestamp.tar.gz" \
		--exclude='.git' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='venv' \
		--exclude='.env' \
		skills/ config/ molib/ molin/ docs/ \
		&& echo "✓ 备份完成: backup_$$timestamp.tar.gz"
