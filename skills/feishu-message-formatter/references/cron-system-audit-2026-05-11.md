# Cron 系统完整审计 · 2026-05-11

> 19 个定时任务的全量审计：每个任务的完整 prompt、引用技能、脚本源码、依赖关系、错误状态。

---

## 19 任务全景

| # | 作业ID | 名称 | 类型 | 时间 | 状态 |
|---|--------|------|------|------|------|
| 1 | 0efd1c5f13d0 | 墨麟OS每日系统备份 | 脚本(molin_backup.sh) | 03:00 | ✅ |
| 2 | bfa036c70aad | 夸克云盘增量备份 | 脚本(molin_backup.sh) | 07:00 | ✅ |
| 3 | d55f171fc48b | GitHub双向同步 | 脚本(molin_sync.sh) | 每2h | ✅ |
| 4 | 60d1ae7ef880 | API成本预警检查 | Agent | 07:30 | ❌→✅ |
| 5 | 8ea1aeb189c3 | 墨梦记忆周度蒸馏 | Agent | 周一06:00 | ❌ |
| 6 | bf670fd0a49d | 墨思情报银行每日扫描 | Agent(飞轮第一棒) | 08:00 | ❌ |
| 7 | 314276cd60e8 | GitHub技术雷达每日扫描 | Agent | 08:00 | ✅ |
| 8 | 9bdd1bf3a6b7 | CEO每日简报 | Agent | 09:00 | ❌ |
| 9 | 8d3480b7a03e | 墨迹内容工厂飞轮 | Agent(飞轮第二棒) | 09:00 | ❌ |
| 10 | 1a6bd56a00cc | 闲鱼消息检测 | Agent | 09:15起/30min | ✅ |
| 11 | 67655653eaf3 | 每日治理合规检查 | Agent | 10:00 | ✅ |
| 12 | e2d424db0a17 | 墨增增长引擎接力 | Agent(飞轮第三棒) | 10:00 | ✅ |
| 13 | c0fe8283335d | 自学习每周进化 | Agent | 周五10:00 | 未跑 |
| 14 | a279d1076e31 | 技能库健康审计 | Agent | 每月15日10:00 | 未跑 |
| 15 | 3973c2d38acf | 内容效果回收分析 | Agent | 11:00 | ✅ |
| 16 | cd7f45ea8088 | 系统健康快照 | Agent | 12:00 | ✅ |
| 17 | ec894b8ebdae | 竞品价格内容监控 | Agent | 14:00 | ✅ |
| 18 | 7d73716dbf68 | CEO下班汇总简报 | Agent | 17:00 | 未跑 |
| 19 | 6c951a667351 | 月度财务对账报告 | Agent | 每月1日09:00 | 未跑 |

---

## 飞轮三级接力链（关键架构）

```
08:00 情报银行(第一棒) → relay/intelligence_morning.json
    ↓
09:00 内容工厂(第二棒) → 读取情报 → relay/content_flywheel.json
    ↓
10:00 增长引擎(第三棒) → 读取内容 → relay/growth_flywheel.json
```

**断裂条件**: 第一棒失败 → 第二棒读取不到 intelligence_morning.json → 空转或静默失败
**修复**: 第二、三棒前置 `flywheel_guard.check_upstream()` 检查上游文件存在且 <90分钟

---

## HTTP 402 问题诊断与修复

### 诊断
- 2026-05-11 07:00-09:15 期间，5个任务全部报 `HTTP 402: Insufficient Balance`
- 实际余额: ¥77.40（充足）
- 直接 API 调用: HTTP 200（正常）
- 根本原因: `deepseek-v4-pro` 临时计费系统故障，10:00后自愈

### 修复方案: fallback_model
在 `~/.hermes/config.yaml` 添加:
```yaml
fallback_model: deepseek-v4-flash
```

**工作原理:**
- cron 调度器每 tick 读取 `fallback_model`，传给 AIAgent
- 当 v4-pro 返回 402 等错误时，自动降级到 v4-flash
- 同 Provider(deepseek)、同 API Key，零额外配置
- 全局生效，不需要修改任何一个 cron 任务

**v4-flash 优势:**
- 价格是 v4-pro 的 ~50%
- cron 任务（结构化报告/数据汇总/消息检测）不需要深度推理
- 更稳定（较少计费系统故障）

---

## 三个备份脚本

### molin_backup.sh (182行)
```
Step 1: 导出 ~/.hermes/skills/ → ~/Molin-OS/skills/
Step 2: 导出 cron.db + jobs.yaml → ~/Molin-OS/backup/
Step 3: git pull --rebase + git push origin main
Step 4: rsync → /Volumes/MolinOS/hermes/（排除 venv/cache/logs/sessions）
Step 5: 清理7天前 /tmp/molin_backup_*.log
```
被 03:00 和 07:00 两个 job 调用（冗余）

### molin_sync.sh (95行)
```
Step 0: git pull --rebase
Step 1: 清空+重导 ~/.hermes/skills/ → ~/Molin-OS/skills/
Step 2: git add molib/ registry/ molin-skills/
Step 3: 同步 cron.db + xianyu config + scripts
Step 4: git commit（无变更跳过）
Step 5: git push
```
每2h执行，12次/天，大部分无变更

### xianyu_check.py (63行)
```
检查 cookies.json → TLS修复 → API Token验证
输出: JSON {status, token_ok, error, cookies_ok}
依赖: Molin-OS/molib/xianyu/ goofish_apis + utils
```

---

## 六大待修复问题

| ID | 问题 | 严重度 |
|----|------|--------|
| CRON-01 | HTTP 402 余额不足：5个核心任务失败，飞轮断裂 | 🔴 严重 |
| CRON-02 | 并发冲突：08:00/09:00/10:00 各有2-3任务同时启动 | 🟡 中等 |
| CRON-03 | 无工作日感知：周六日也在跑业务任务，浪费30%预算 | 🟡 中等 |
| CRON-04 | 备份重复：molin_backup.sh 03:00和07:00重复执行 | 🟢 低 |
| CRON-05 | GitHub同步过频：每2h×12次/天，大部分无变更 | 🟢 低 |
| CRON-06 | 无上下班节点：CEO简报09:00太早，下班汇总17:00太早 | 🟡 中等 |

CRON-01 已修复（fallback_model），其余待实施。

---

## 引用技能清单（27个）

全量列表见完整审计输出。最常引用的3个:
- `feishu-message-formatter` (13次)
- `molin-ceo-persona` (3次)
- `molin-goals` (2次)
