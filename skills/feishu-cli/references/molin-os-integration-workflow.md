# 墨麟OS × Hermes Agent 完整融合工作流

> 记录 2026-05-10 会话中完成的完整融合过程。适用于任何需要"外挂 Python 项目深度集成到 Hermes"的场景。

## 前置条件

- Hermes Agent 已安装运行
- GitHub repo（私有/公开均可）
- Python ≥ 3.10 项目

## 七步融合法

### 1. GitHub 认证

```bash
# 如无 gh CLI，用 git credential store 方式
git config --global credential.helper store
git config --global user.name "username"
git config --global user.email "email"
git ls-remote https://username:TOKEN@github.com/owner/repo.git HEAD
```

Token 存到 `~/.hermes/.env`：`GITHUB_TOKEN=xxx`

### 2. 克隆项目

```bash
git clone https://username:TOKEN@github.com/owner/repo.git ~/project-name
```

网速慢时 VPN 是必需品。

### 3. 安装到 Hermes venv（editable）

Hermes venv 自带 Python 但不带 pip：

```bash
# 引导 pip
~/.hermes/hermes-agent/venv/bin/python -m ensurepip

# editable 安装，修改源码即时生效
~/.hermes/hermes-agent/venv/bin/python -m pip install -e ~/project-name
```

**致命坑**：Hermes 的 system Python（`~/.local/bin/python3.11`）是 uv 管理的 externally-managed 环境，`pip install` 会报错。**必须用 Hermes venv 内的 Python**。

**PyPI 超时**：国内直连 PyPI 大概率 ReadTimeoutError。换阿里云镜像：
```bash
~/.hermes/hermes-agent/venv/bin/python -m pip install -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com pkg1 pkg2 ...
```

### 4. 注入环境变量

项目可能有自己的 `.env.example`，对照补全到 `~/.hermes/.env`。

**硬编码密钥提取模式**：扫描项目中硬编码的 API Key，提取到环境变量：
```bash
grep -rn "API_KEY\|SECRET\|TOKEN.*=.*[\"']" ./project/ --include="*.py" | grep -v ".pyc"
```

### 5. 技能迁移

```bash
MOLIN_SKILLS=~/project-name/skills
HERMES_SKILLS=~/.hermes/skills

# 批量迁移（含子目录）
for cat_dir in "$MOLIN_SKILLS"/*/; do
    for skill_dir in "$cat_dir"/*/; do
        skill_name=$(basename "$skill_dir")
        [ ! -d "$HERMES_SKILLS/$skill_name" ] && cp -r "$skill_dir" "$HERMES_SKILLS/"
    done
done
```

### 6. 创建定时作业

```bash
# 对照项目的 cron/jobs.yaml，逐个创建
hermes cron create "作业名" \
  --schedule "0 8 * * *" \
  --skills '["skill1","skill2"]' \
  --deliver "feishu:chat_id"
```

### 7. 注册基础设施

- MCP Server → 写入 `config.yaml` 的 `mcp_servers` 段
- 记忆目录 → `mkdir -p ~/.hermes/memory/{long_term,chroma_db}`
- Provider 注册 → `config.yaml` 的 `providers` 段
- 辅助模型 → `config.yaml` 的 `auxiliary.vision.*` 段

## 验证清单

- [ ] `python -m molib health` 全绿
- [ ] `hermes cron list` 作业已创建
- [ ] 技能数大幅增长（>100 表示迁移充分）
- [ ] `feishu-cli --version` 输出正常
- [ ] 视觉模型 `curl` 测试通过
- [ ] `grep -r "chat_id\|NOTIFY_CHAT" ~/project/bots/` 找到自动化群 ID
