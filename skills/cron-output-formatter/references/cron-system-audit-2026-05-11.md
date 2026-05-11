# Cron 系统审计 — 2026-05-11

## 触发背景

用户要求梳理全部 19 个定时任务，发现 6 大问题后进行系统性重构。

## 19 任务完整清单

| # | job_id | 名称 | 类型 | 重构动作 |
|---|--------|------|------|---------|
| 1 | 0efd1c5f13d0 | 墨麟OS每日系统备份 | 脚本(molin_backup.sh) | 保留 03:00 |
| 2 | bfa036c70aad | 夸克云盘增量备份→轻量同步 | 脚本(molin_light.sh) | 改为轻量脚本 |
| 3 | d55f171fc48b | GitHub双向同步 | 脚本(molin_sync.sh) | 12次/天→3次/天(工作日) |
| 4 | 60d1ae7ef880 | API成本预警检查 | Agent | 工作日 07:30 |
| 5 | bf670fd0a49d | 墨思情报银行(飞轮第一棒) | Agent | 工作日 08:00 |
| 6 | 314276cd60e8 | GitHub技术雷达 | Agent | 工作日 08:30 |
| 7 | 9bdd1bf3a6b7 | CEO每日简报 | Agent | 工作日 09:00 |
| 8 | 8d3480b7a03e | 墨迹内容工厂(飞轮第二棒) | Agent | 工作日 09:20 |
| 9 | 1a6bd56a00cc | 闲鱼消息检测 | Agent | 工作日 09:45-17:45 |
| 10 | 67655653eaf3 | 每日治理合规检查 | Agent | 工作日 10:00 |
| 11 | e2d424db0a17 | 墨增增长引擎(飞轮第三棒) | Agent | 工作日 10:45 |
| 12 | 3973c2d38acf | 内容效果回收分析 | Agent | 工作日 11:00 |
| 13 | cd7f45ea8088 | 系统健康快照 | Agent | 工作日 12:00 |
| 14 | ec894b8ebdae | 竞品价格内容监控 | Agent | 工作日 14:00 |
| 15 | 7d73716dbf68 | CEO下班汇总 | Agent | 工作日 18:28 |
| 16 | 8ea1aeb189c3 | 墨梦记忆周度蒸馏 | Agent | 周一 06:00 |
| 17 | c0fe8283335d | 自学习进化 | Agent | 周五 10:30 |
| 18 | a279d1076e31 | 技能健康审计 | Agent | 每月15日 |
| 19 | 6c951a667351 | 月度财务对账 | Agent | 每月1日 |

## 六大问题及修复

1. **HTTP 402 余额不足** → config.yaml 添加 `fallback_model: deepseek-v4-flash`
2. **并发冲突 08/09/10** → 错峰: 08:00→09:20→10:45
3. **无工作日感知** → 所有业务任务加 `Mon-Fri` 约束，周末仅保留备份+闲鱼/2h
4. **备份重复** → 07:00 改为 molin_light.sh (~15s vs 3min)
5. **GitHub同步过频** → 12次→3次/天
6. **上下班节点不对** → CEO简报 09:28推送，下班汇总 18:28

## exfil_curl_auth_header 过滤器

### 发现过程
更新 cron prompt 时嵌入 `curl -H "Authorization: Bearer $KEY"` 被拒绝。
排查发现 `feishu-message-formatter/SKILL.md` 中的代码示例也包含类似模式，
cron scheduler 加载该技能时被整包拒绝。

### 解决方案
创建 `cron-output-formatter` — 纯规则无代码的 cron-safe 版格式化技能。
所有 19 个 cron 任务的 skills 从 `feishu-message-formatter` 切换为 `cron-output-formatter`。

### 关键教训
- Cron prompt 和加载的技能都会被扫描 `exfil_curl_auth_header` 模式
- 任何含 `Authorization: Bearer` 或 `curl.*api_key` 的 SKILL.md 都不能被 cron 加载
- 解决方案：创建 cron-safe 版本（纯规则，无代码示例）

## 飞轮依赖修复

创建 `molib/shared/flywheel_guard.py`:
- `check_upstream(file, max_age)` — 检查上游 relay 文件是否存在且新鲜
- `flywheel_abort_if_broken(file, task_name)` — 上游断链时 T4 告警+退出
- `flywheel_health_check()` — 全链路健康检查

内容工厂(09:20)和增长引擎(10:45)的 prompt 中添加了前置依赖检查。
