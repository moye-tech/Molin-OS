# 墨麟OS · 定时任务 & 内容规则全览

> 审计时间: 2026-05-11 14:30 CST · 共 19 个定时任务 + 4 棒飞轮管线

---

## ⏱️ 每日时间线

```
03:00  ██ 系统备份 (no_agent)
06:00  ██ 记忆蒸馏 (周一)
07:00  ██ 夸克云盘备份 (no_agent)
07:30  ██ API成本预警
08:00  ██ 墨思情报银行扫描 ⚡
08:00  ██ GitHub技术雷达扫描 ⚡
09:00  ██ CEO简报
09:00  ██ 墨迹内容工厂飞轮 ⚡
10:00  ██ 墨增增长引擎接力 ⚡
10:00  ██ 治理合规检查
10:00  ██ 自学习每周进化 (周五)
10:00  ██ 技能库健康审计 (每月15日)
11:00  ██ 内容效果回收分析
12:00  ██ 系统健康快照
14:00  ██ 竞品价格内容监控
17:00  ██ CEO下班简报
全天    ██ 闲鱼消息检测 (9-21点，每30分钟)
全天    ██ GitHub双向同步 (每2小时)
```

---

## 一、LLM Agent 任务 (13 个)

> 有 prompt + skills，Agent 自主推理执行。

### 1. GitHub 技术雷达 · 每日扫描
| 属性 | 值 |
|:--|:--|
| **ID** | `314276cd60e8` |
| **时间** | `0 8 * * *` (每日 08:00) |
| **Skill** | `github-trending-scanner` |
| **工具集** | `web` `terminal` `file` |
| **交付** | 飞书自动化控制台群 + 当前对话 |
| **上次状态** | ✅ ok |

**内容规则:**
```
Step 1: 发现 (15-20个候选)
  → web_search "GitHub trending projects today"
  → 扫描 30-50 个 Trending 项目

Step 2: 筛选 (Top 5-10)
  → 匹配 Molin-OS 22家子公司能力矩阵
  → 评分维度: 架构匹配/能力提升/部署成本/维护性

Step 3: 架构匹配评分
  → 7层评分 × 权重矩阵
  → 输出结构化日报 → 飞书卡片

Step 4: 存档
  → ~/.hermes/daily_reports/github_radar_{date}.md
  → SuperMemory 云端同步
```

---

### 2. 墨思情报银行 · 每日扫描 (飞轮第一棒)
| 属性 | 值 |
|:--|:--|
| **ID** | `bf670fd0a49d` |
| **时间** | `0 8 * * *` (每日 08:00) |
| **Skills** | `blogwatcher` `arxiv` `firecrawl` `karpathy-autoresearch` `feishu-message-formatter` |
| **交付** | 飞书自动化控制台群 |
| **上次状态** | ❌ error |

**内容规则:**
```
1. blogwatcher 扫描订阅博客
2. arxiv 搜索最新 AI 论文 (cs.AI, cs.CL, cs.LG)
3. firecrawl search 搜索网络热点
4. karpathy-autoresearch 深度研究 Top 3
5. 写入 relay/intelligence_morning.json (接力给下一棒)
6. 生成飞书卡片推送
```

**接力输出:** `relay/intelligence_morning.json`

---

### 3. 墨迹内容工厂飞轮 (飞轮第二棒)
| 属性 | 值 |
|:--|:--|
| **ID** | `8d3480b7a03e` |
| **时间** | `0 9 * * *` (每日 09:00) |
| **Skills** | `agent-marketing-content-creator` `seo-machine` `ffmpeg-video-engine` `feishu-message-formatter` |
| **交付** | 飞书自动化控制台群 |
| **上次状态** | ❌ error |

**内容规则:**
```
1. 读取 relay/intelligence_morning.json 情报数据
2. agent-marketing-content-creator 生成内容 (小红书/公众号/微博)
3. seo-machine 优化标题和关键词
4. 写入 relay/content_flywheel.json (接力给下一棒)
5. 如有视频素材，用 ffmpeg-video-engine 生成短视频
```

**接力输入:** `relay/intelligence_morning.json`
**接力输出:** `relay/content_flywheel.json`

---

### 4. 墨增增长引擎接力 (飞轮第三棒)
| 属性 | 值 |
|:--|:--|
| **ID** | `e2d424db0a17` |
| **时间** | `0 10 * * *` (每日 10:00) |
| **Skills** | `claude-seo` `seo-audit` `analytics-tracking` `content-strategy` `agent-marketing-growth-hacker` `feishu-message-formatter` |
| **交付** | 飞书自动化控制台群 |
| **上次状态** | ✅ ok |

**内容规则:**
```
1. 读取 relay/content_flywheel.json
2. claude-seo 做搜索引擎优化
3. seo-audit 审计内容 SEO 质量
4. analytics-tracking 追踪内容表现
5. content-strategy 更新内容策略
6. agent-marketing-growth-hacker 制定增长方案
7. 写入 relay/distribution_plan.json
```

**接力输入:** `relay/content_flywheel.json`
**接力输出:** `relay/distribution_plan.json`

---

### 🔗 飞轮三棒接力协议

```
08:00  [情报] intelligence_morning.json ──→ 09:00 [内容] content_flywheel.json ──→ 10:00 [增长] distribution_plan.json
         ↑                                    ↑                                    ↑
    墨思情报银行                         墨迹内容工厂                         墨增增长引擎
```

**关键规则:**
1. 每棒必须先检查 `relay/` 中是否有上一棒的文件
2. 如果没有 → 用上次可用数据或跳过
3. 文件格式严格对齐: `intelligence_morning.json → content_flywheel.json → distribution_plan.json`
4. 符号链接: `content_flywheel.json` → `content_flywheel_{date}.json` (保留历史)

---

### 5. CEO 简报
| 属性 | 值 |
|:--|:--|
| **ID** | `9bdd1bf3a6b7` |
| **时间** | `0 9 * * *` (每日 09:00) |
| **Skills** | `molin-ceo-persona` `molin-goals` `feishu-message-formatter` |
| **上次状态** | ❌ error |

**内容规则:**
```
1. 检查昨天产出 (内容/情报/闲鱼消息)
2. 列出今日待办
3. 检测系统健康状态
4. 严格遵循 feishu-message-formatter CEO 规范
```

---

### 6. CEO 下班简报
| 属性 | 值 |
|:--|:--|
| **ID** | `7d73716dbf68` |
| **时间** | `0 17 * * *` (每日 17:00) |
| **Skills** | `molin-ceo-persona` `molin-goals` `feishu-message-formatter` |

**内容规则:**
```
汇总今日全部产出，生成 CEO 下班简报飞书卡片:
  - 今日产出清单
  - 财务概览
  - 明日待办
  - 风险提示
严格遵循 feishu-message-formatter CEO 规范
```

---

### 7. 系统健康快照
| 属性 | 值 |
|:--|:--|
| **ID** | `cd7f45ea8088` |
| **时间** | `0 12 * * *` (每日 12:00) |
| **Skills** | `molin-company-structure` `molin-ceo-persona` `feishu-message-formatter` |
| **上次状态** | ✅ ok |

**内容规则:**
```
1. 运行 python -m molib health 检查系统状态
2. 用 session_search 查询今日活跃会话
3. 生成结构化快照卡片 → 飞书推送
```

---

### 8. 治理合规检查
| 属性 | 值 |
|:--|:--|
| **ID** | `67655653eaf3` |
| **时间** | `0 10 * * *` (每日 10:00) |
| **Skills** | `molin-governance` `feishu-message-formatter` |
| **上次状态** | ✅ ok |

**内容规则:**
```
1. 加载 molin-governance 技能
2. 检查过去24小时所有 L1/L2 操作是否合规
3. 审计日志扫描
4. L2 待审批项上报
5. 生成合规报告推送
```

---

### 9. 闲鱼消息检测
| 属性 | 值 |
|:--|:--|
| **ID** | `1a6bd56a00cc` |
| **时间** | `15,45 9-21 * * *` (每日 9:00-21:00, 每30分钟) |
| **Skills** | `xianyu-automation` `agent-sales-deal-strategist` `marketing-skills-copywriting` `feishu-message-formatter` |
| **上次状态** | ✅ ok |

**内容规则:**
```
1. 运行 python /Users/moye/.hermes/scripts/xianyu_check.py 检查新消息
2. 若有新消息 → agent-sales-deal-strategist 分析买家意图
3. marketing-skills-copywriting 生成回复话术
4. 生成巡检卡片推送
```

---

### 10. API 成本预警检查
| 属性 | 值 |
|:--|:--|
| **ID** | `60d1ae7ef880` |
| **时间** | `30 7 * * *` (每日 07:30) |
| **Skills** | `feishu-message-formatter` |
| **上次状态** | ❌ error |

**内容规则:**
```
统计昨日 DeepSeek/DashScope API 消耗:
  - python -m molib cost report 获取数据
  - 超过日预算 80% → 飞书告警
  - 遵循 feishu-message-formatter CEO 规范
```

---

### 11. 内容效果回收分析
| 属性 | 值 |
|:--|:--|
| **ID** | `3973c2d38acf` |
| **时间** | `0 11 * * *` (每日 11:00) |
| **Skills** | `analytics-tracking` `content-strategy` `feishu-message-formatter` |
| **上次状态** | ✅ ok |

**内容规则:**
```
抓取昨日发布内容的 阅读/点赞/收藏 数据:
  - 汇总 Top 3 爆款 + Bottom 3 低效内容
  - 给出优化建议
  - 遵循 feishu-message-formatter CEO 规范
```

---

### 12. 竞品价格内容监控
| 属性 | 值 |
|:--|:--|
| **ID** | `ec894b8ebdae` |
| **时间** | `0 14 * * *` (每日 14:00) |
| **Skills** | `competitor-analysis` `mirofish-trends` `feishu-message-formatter` |
| **上次状态** | ✅ ok |

**内容规则:**
```
用 Scrapling 抓取竞品闲鱼定价、小红书爆款:
  - 异常变动 → 飞书通知
  - 对比自身商品定价
  - 给出调价建议
  - 遵循 feishu-message-formatter CEO 规范
```

---

### 13. 🗓️ 周期任务 (3 个)

#### 13a. 自学习每周进化 (周五 10:00)
| 属性 | 值 |
|:--|:--|
| **ID** | `c0fe8283335d` |
| **时间** | `0 10 * * 5` (每周五 10:00) |
| **Skills** | `skill-discovery` `self-learning-loop` `karpathy-autoresearch` `feishu-message-formatter` |

**内容规则:**
```
1. session_search 回顾本周所有复杂任务
2. skill-discovery 扫描外部新技能
3. self-learning-loop 提炼经验到技能库
4. 遵循 feishu-message-formatter CEO 规范
```

#### 13b. 墨梦记忆周度蒸馏 (周一 06:00)
| 属性 | 值 |
|:--|:--|
| **ID** | `8ea1aeb189c3` |
| **时间** | `0 6 * * 1` (每周一 06:00) |
| **Skills** | `self-learning-loop` `molin-memory` `feishu-message-formatter` |
| **上次状态** | ❌ error |

**内容规则:**
```
整合上周 relay/ 文件和对话记录:
  → 提炼 SOP 模式 → 更新对应子公司 SKILL.md
  → 三层记忆蒸馏: 工作记忆→情节记忆→语义记忆
  → 检查 30 天未用技能并归档
```

#### 13c. 技能库健康审计 (每月15日 10:00)
| 属性 | 值 |
|:--|:--|
| **ID** | `a279d1076e31` |
| **时间** | `0 10 15 * *` (每月15日 10:00) |
| **Skills** | `skill-quality-eval` `feishu-message-formatter` |

**内容规则:**
```
检查所有 SKILL.md 最后调用时间:
  - 识别 30 天未用技能
  - python -m molib query "FROM skills SORT BY modified_at ASC"
  - 遵循 feishu-message-formatter CEO 规范
```

#### 13d. 月度财务对账报告 (每月1日 09:00)
| 属性 | 值 |
|:--|:--|
| **ID** | `6c951a667351` |
| **时间** | `0 9 1 * *` (每月1日 09:00) |
| **Skills** | `feishu-message-formatter` |

**内容规则:**
```
汇总本月收入/支出/API成本/利润率:
  - python -m molib finance report
  - 对比上月和预算
  - 遵循 feishu-message-formatter CEO 规范
```

---

## 二、Shell 脚本任务 (3 个 no_agent)

> 无 LLM 推理，纯 shell 脚本执行。

### 14. 墨麟OS 每日系统备份
| 属性 | 值 |
|:--|:--|
| **ID** | `0efd1c5f13d0` |
| **时间** | `0 3 * * *` (每日 03:00) |
| **脚本** | `molin_backup.sh` |
| **模式** | `no_agent: true` |
| **上次状态** | ✅ ok |

**规则:** 双目标备份 → GitHub (代码+技能) + 本地硬盘 (全量含密钥)

---

### 15. 夸克云盘增量备份
| 属性 | 值 |
|:--|:--|
| **ID** | `bfa036c70aad` |
| **时间** | `0 7 * * *` (每日 07:00) |
| **脚本** | `molin_backup.sh` |
| **模式** | `no_agent: true` |
| **上次状态** | ✅ ok |

---

### 16. 墨麟OS GitHub 双向同步
| 属性 | 值 |
|:--|:--|
| **ID** | `d55f171fc48b` |
| **时间** | `0 */2 * * *` (每 2 小时) |
| **脚本** | `molin_sync.sh` |
| **模式** | `no_agent: true` |
| **上次状态** | ✅ ok |

**规则:** `git pull → 检查冲突 → git push` 确保 GitHub 始终与本地一致

---

## 三、问题汇总

| # | 任务 | 状态 | 建议 |
|:--|:--|:--|:--|
| 1 | 墨思情报银行 | ❌ error | 需排查 blogwatcher/arxiv API 是否可用 |
| 2 | 墨迹内容工厂 | ❌ error | 依赖情报银行 → 情报银行修好后自然恢复 |
| 3 | CEO 简报 | ❌ error | 需排查 molin-goals skill 加载 |
| 4 | API 成本预警 | ❌ error | 需排查 `molib cost report` CLI |
| 5 | 墨梦记忆蒸馏 | ❌ error | 需排查 self-learning-loop 是否正常 |

### 冲突时间点

| 时间 | 冲突任务 |
|:--|:--|
| 08:00 | 情报银行 + GitHub雷达 (同时触发) |
| 09:00 | CEO简报 + 内容工厂 (同时触发) |
| 10:00 | 增长引擎 + 治理合规 (+ 周五自学习) |

---

## 四、优化建议速查

| 优先级 | 建议 |
|:--|:--|
| 🔴 P0 | 修复 5 个 error 状态任务 |
| 🟡 P1 | 错开 08:00/09:00/10:00 冲突 (各延迟5分钟) |
| 🟡 P1 | CEO上/下班简报合并为一个日报+晚报模式 |
| 🟢 P2 | 情报银行+GitHub雷达合并为一个综合情报任务 |
| 🟢 P2 | 内容工厂+增长引擎合并为一个端到端 pipeline |
| 🟢 P2 | 备份任务去重 (3个备份 → 1个统一备份) |
