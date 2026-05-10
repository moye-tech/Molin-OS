# Molin-OS 集成到 Hermes Agent 工作流

## 前置条件

- Hermes Agent 已安装，venv 在 `~/.hermes/hermes-agent/venv`
- Molin-OS 仓库已 clone 到 `~/Molin-OS`
- GitHub 认证已配置（Token + git identity）

## 集成步骤

### 1. Hermes venv 需要 pip

Hermes 的 venv 默认精简，无 pip。先引导：

```bash
~/.hermes/hermes-agent/venv/bin/python -m ensurepip
```

注意：venv 里没有 `venv/bin/pip` 二进制，只能用 `python -m pip`。

### 2. 安装 molib 为 editable package

```bash
cd ~/Molin-OS
~/.hermes/hermes-agent/venv/bin/python -m pip install -e .
```

核心依赖（`pyyaml`, `python-dotenv`, `click`, `rich`, `requests`）通常已存在。

### 3. 修复 __version__ 缺失

`molib/__init__.py` 默认没有 `__version__`，但 `__main__.py` 导入了它。需添加：

```python
__author__ = "moye-tech"
__version__ = "5.0.0"
```

### 4. 验证

```bash
cd ~/Molin-OS
~/.hermes/hermes-agent/venv/bin/python -m molib health
```

预期输出：所有模块 `✅ ok`，`status: "ok"`。

## 关键陷阱

- **不要用系统 Python**：系统级别 Python 3.11 由 uv 管理（`externally-managed-environment`），拒绝 pip install
- **不要创建独立 venv**：Molin-OS 设计上跑在 Hermes 的 venv 里，独立 venv 会导致路径不一致
- **不要动 Hermes config**：Molin-OS 是叠加层，不修改 `config.yaml` 或 `.env`
- **`python -m molib` 不是 `python -m molin`**：入口是 `molib`，不是 `molin`

## 技能迁移

Molin-OS 的 155 个技能在 `~/Molin-OS/skills/` 中按类别分目录（`content/`, `growth/`, `meta/` 等），需要扁平化复制到 `~/.hermes/skills/`：

```bash
for cat_dir in ~/Molin-OS/skills/*/; do
    cat_name=$(basename "$cat_dir")
    [ "$cat_name" = "absorbed" ] && continue
    for skill_dir in "$cat_dir"/*/; do
        skill_name=$(basename "$skill_dir")
        [ ! -d ~/.hermes/skills/"$skill_name" ] && cp -r "$skill_dir" ~/.hermes/skills/"$skill_name"
    done
done
```

## feishu-cli 并行安装

feishu-cli 是 Go 二进制，独立于 Hermes Python 环境：

```bash
# 需要 VPN
curl -fsSL https://raw.githubusercontent.com/riba2534/feishu-cli/main/install.sh | bash
```

凭证复用 `~/.hermes/.env` 中的 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`。

## 外部项目完整集成模式

将第三方项目（如 Firecrawl、9Router 等）集成到 Molin-OS 时，遵循四层模式：

### 层级结构

```
1. SDK/依赖层    → pip install 到 Hermes venv
2. 技能层        → ~/.hermes/skills/<name>/SKILL.md（完整 API 文档）
3. molib 模块层   → molib/<domain>/<name>_client.py（Python 封装 + CLI）
4. Cron 接入层    → 更新相关 cron job 的 skills 列表和 prompt
```

### 集成清单

- SDK 安装到 Hermes venv
- SKILL.md 覆盖全部 API（不可简化）
- molib 模块：独立 .py 文件，自带 `_cli()` 入口
- `__main__.py` 注册子命令（`cmd_intel` 等函数中 `if subcmd == "xxx"` 分支）
- `cmd_help` 函数中添加命令文档
- 相关 cron job 加载新技能
- API Key 写入 `~/.hermes/.env`
- 变更提交到 GitHub + 本地硬盘备份

### Firecrawl 集成实例

```
SDK: firecrawl-py v4.25.2
技能: ~/.hermes/skills/intelligence/firecrawl/SKILL.md
模块: molib/intelligence/firecrawl_client.py (scrape/crawl/search/batch/research/map)
CLI: python -m molib intel firecrawl scrape --url URL
Cron: 墨思情报银行 (bf670fd0a49d) 已加载 firecrawl 技能
```
