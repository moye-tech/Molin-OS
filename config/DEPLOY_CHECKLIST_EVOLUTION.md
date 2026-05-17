# 墨麟OS 进化体系 — 部署清单
# 本批次新增文件完整部署指引
# 生成日期：2026-05-17
# ─────────────────────────────────────────────────────────

## 一、文件清单与目标路径

### 1. SOP定义文件（5个）
复制到 `Molin-OS/sop/definitions/`

| 文件名 | 目标路径 | 优先级 |
|--------|----------|--------|
| auto_dream_sop.yaml | sop/definitions/auto_dream_sop.yaml | 🔴 最高 |
| data_analyst_sop.yaml | sop/definitions/data_analyst_sop.yaml | 🔴 最高 |
| ip_management_sop.yaml | sop/definitions/ip_management_sop.yaml | 🟡 高 |
| security_proactive_audit_sop.yaml | sop/definitions/security_proactive_audit_sop.yaml | 🟡 高 |
| crm_private_domain_sop.yaml | sop/definitions/crm_private_domain_sop.yaml | 🟢 中（待基建） |

### 2. Cron配置文件（1个，包含7个新Job）
合并到现有 `backup/jobs.yaml`，或单独加载：

| 文件名 | 目标路径 |
|--------|----------|
| cron_evolution_plan.yaml | config/cron_evolution_plan.yaml |

### 3. 学习订阅配置（1个）
| 文件名 | 目标路径 |
|--------|----------|
| agent_learning_subscriptions.yaml | config/learning/agent_learning_subscriptions.yaml |

### 4. 脚本文件（2个）
| 文件名 | 目标路径 | 权限 |
|--------|----------|------|
| github_vertical_scan.py | scripts/github_vertical_scan.py | chmod +x |
| init_obsidian_taxonomy.py | scripts/init_obsidian_taxonomy.py | chmod +x |

---

## 二、激活步骤（按顺序执行）

### Step 0 — 前置检查（必须，5分钟）

```bash
# 检查SOP Engine开关
grep "SOP_AUTOMATION_ENABLED" .env || echo "⚠️ 未设置，需添加"

# 检查GitHub Token
echo $GITHUB_TOKEN | cut -c1-8  # 只打印前8位，确认存在

# 检查Obsidian Vault路径
echo $OBSIDIAN_VAULT_PATH
ls $OBSIDIAN_VAULT_PATH 2>/dev/null || echo "⚠️ Vault路径不存在"

# 检查DeepSeek API Key
echo $DEEPSEEK_API_KEY | cut -c1-8
```

### Step 1 — 开启SOP自动化（1分钟）

在 `.env` 文件中添加：

```bash
# SOP自动化总开关（原来默认false）
SOP_AUTOMATION_ENABLED=true

# 学习飞轮配置
GITHUB_TOKEN=ghp_yo...here
OBSIDIAN_VAULT_PATH=/Users/laomo/Library/Mobile Documents/iCloud~md~obsidian/Documents  # v3.0 flat vault  # 改为你的实际路径

# 深度笔记最低字符数
DEEP_NOTE_MIN_CHARS=800

# EvolutionEngine质量门槛
EVOLUTION_SCORE_THRESHOLD=7.5
```

验证SOP Engine加载：
```bash
python -m molib validate
# 预期输出：✅ 27/27 SOP definitions loaded（原22个+本批次5个）
```

### Step 2 — 初始化Obsidian目录（2分钟）

```bash
# 首次初始化
# ⚠️ SKIPPED: init_obsidian_taxonomy.py creates OLD subdirectory structure, incompatible with v3.0 flat vault

# 检查目录结构
ls "/Users/laomo/Library/Mobile Documents/iCloud~md~obsidian/Documents/"
# v3.0 flat: 决策/ 知识/ 流程/ 成果/ 报告/ 配置/ 产出/ 学习档案/
```

### Step 3 — 部署SOP文件（1分钟）

```bash
cp sop/definitions/auto_dream_sop.yaml sop/definitions/
cp sop/definitions/data_analyst_sop.yaml sop/definitions/
cp sop/definitions/ip_management_sop.yaml sop/definitions/
cp sop/definitions/security_proactive_audit_sop.yaml sop/definitions/
cp sop/definitions/crm_private_domain_sop.yaml sop/definitions/

# 验证
python -m molib sop list | grep -E "auto_dream|data_analyst|ip_management|security_proactive|crm_private"
```

### Step 4 — 安装Cron（2分钟）

```bash
# 方案A：合并到主jobs.yaml（推荐）
cat config/cron_evolution_plan.yaml >> backup/jobs.yaml

# 方案B：单独文件加载
molin cron init --file config/cron_evolution_plan.yaml

# 验证7个新Cron已注册
molin cron list | grep -E "learn_a|plan_b|audit_c"
```

### Step 5 — 测试学习扫描脚本（5分钟）

```bash
# 先用dry-run验证配置正确
python3 scripts/github_vertical_scan.py --dry-run

# 单Agent测试（不用等全部5个）
python3 scripts/github_vertical_scan.py --agent mobi_edu

# 检查输出
cat relay/learning/mobi_edu_scan_$(date +%Y%m%d).json | python3 -m json.tool | head -30
```

### Step 6 — 验证记忆分类规则（可选）

在飞书机器人发送测试消息，确认：
- 策略讨论 → 写入 Supermemory（profile=CEO）
- 任务指令完成 → 写入 # v3.0 flat: 成果/
- 复盘总结 → 写入 /Users/laomo/Library/Mobile Documents/iCloud~md~obsidian/Documents/报告/  # v3.0 flat（字符数≥800强制）

---

## 三、首次运行时间线（本周）

```
今天（周日）
  ├── 21:00 — 记忆蒸馏Cron首次运行（learn_a3）
  │           可能无L2条目，正常
  └── 22:00/22:30 — KPI采集+每日复盘首次运行（plan_b0/b1）

周一
  ├── 06:00 — 垂直GitHub扫描首次运行（learn_a1）⭐ 关键
  ├── 07:00 — AutoDream精读内化首次运行（learn_a2）⭐ 关键
  └── 09:30 — 周计划生成（plan_b2）

下周一 21:00
  └── 质量门控（对本周合并的SKILL打分）
```

---

## 四、CRM SOP Phase 2 启动条件（当前Phase 1）

CRM私域SOP当前为 Phase 1（数据分析+内容规划，需手动发送）。
当以下条件满足时，升级到 Phase 2（自动触达）：

- [ ] 飞书群机器人配置完成（config/channels.yaml 中 feishu_group_bot.enabled=true）
- [ ] LINE Bot Token配置（如需台湾市场）
- [ ] 用户同意书收集完毕（合规要求）

满足后修改 `crm_private_domain_sop.yaml` 中：
```yaml
step_l2_approval:
  governance: L1  # 从 L2 降为 L1
```
并在 step_reach_plan 后添加 auto_send_messages 步骤。

---

## 五、关键约束提醒

| 约束 | 原因 | 处理方式 |
|------|------|----------|
| GitHub API 5000次/小时（有Token） | 5个Agent × 10个查询 = 50次，安全 | 无需特殊处理 |
| 深度笔记 < 800字拒绝写入 | 防止简报混入学习档案 | 模型重试最多2次 |
| SKILL合并需L2审批 | 防止能力退化或引入错误 | 创始人飞书卡片确认 |
| 记忆蒸馏仅压缩30天未调用条目 | 活跃记忆不蒸馏 | 无需关注 |
| 季度基准测试耗时约2小时 | 20个Agent×3个测试 | 安排在10:00，不影响业务 |
| CRM自动触达需Phase 2基建 | 合规+技术双重门槛 | 当前Phase 1手动执行 |