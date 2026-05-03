# 墨麟 Hermes OS — Makefile
# ==========================

.PHONY: help install test lint clean run serve health

# 默认目标
help:
	@echo "墨麟 Hermes OS — 一人公司操作系统"
	@echo ""
	@echo "命令:"
	@echo "  make install     安装依赖"
	@echo "  make setup       完整部署 (setup.sh)"
	@echo "  make test        运行测试"
	@echo "  make lint        代码检查"
	@echo "  make health      健康检查"
	@echo "  make serve       启动Web仪表盘"
	@echo "  make ceo         运行CEO战略"
	@echo "  make content     生成内容"
	@echo "  make xianyu      查看闲鱼商品"
	@echo "  make clean       清理临时文件"
	@echo "  make backup      备份skills和配置"

install:
	pip install -r requirements.txt
	pip install -e .

setup:
	bash setup.sh

test:
	python -m pytest tests/ -v --cov=molin --cov-report=term

lint:
	@echo "代码检查..."
	python -m py_compile molin/*.py molin/*/*.py 2>/dev/null || true
	@echo "✓ 语法检查通过"

health:
	python -c "from molin.core.engine import engine; import json; print(json.dumps(engine.health_check(), indent=2, ensure_ascii=False))"

serve:
	python -c "from molin.dashboard import app; app.run(host='0.0.0.0', port=8080)"

ceo:
	python -m molin.cli ceo strategy

content:
	python -m molin.cli content xhs "AI一人公司必备工具"

xianyu:
	python -m molin.cli xianyu list

intel:
	python -m molin.cli intel trends

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
		skills/ config/ molin/ docs/ \
		&& echo "✓ 备份完成: backup_$$timestamp.tar.gz"
