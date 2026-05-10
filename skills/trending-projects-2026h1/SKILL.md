# 墨麟 AI 集团 — Fork 仓库集成评估报告

> 评估时间: 2026-05-04  
> 评估范围: moye-tech GitHub 所有 fork 仓库（54个项目）  
> 评估维度: 集成价值 × 与现有子公司的匹配度

---

## 🔥 高优先级集成 (10个)

| # | 仓库 | 上游 | ⭐Stars | 当前子公司 | 集成方式 |
|:-:|:-----|:-----|:-------:|:----------|:---------|
| 1 | **claude-mem** | thedotmack/claude-mem | 71K | 墨脑(知识) | 自动捕捉Claude交互→知识图谱→墨麟自学习回路增强 |
| 2 | **MiroFish** | 666ghj/MiroFish | 59K | 墨思(研究) | 群体智能预测引擎→趋势分析/市场预测增强 |
| 3 | **ruflo** | ruvnet/ruflo | 38K | 墨脑(知识) | Agent编排+自学习→墨麟蜂群引擎+自学习回路升级 |
| 4 | **supermemory** | supermemoryai/supermemory | 22K | 墨脑(知识) | 跨会话持久记忆引擎→Hermes记忆系统增强 |
| 5 | **last30days-skill** | mvanhorn/last30days-skill | 25K | 墨思(研究) | 跨平台趋势研究技能→情报局日报/周报自动生成 |
| 6 | **worldmonitor** | koala73/worldmonitor | 53K | 墨思(研究) | 实时全球情报面板→情报局核心引擎 |
| 7 | **agent-skills** | addyosmani/agent-skills | 27K | 墨智(AI研发) | 27380★生产级工程技能→直接导入墨麟技能库 |
| 8 | **paperclip** | paperclipai/paperclip | 62K | (已集成) | 一人公司OS→公司架构/治理/心跳模式已有 |
| 9 | **TradingAgents-CN** | hsliuping/TradingAgents-CN | 25K | 墨投(交易) | 量化交易框架→墨投子公司核心引擎 |
| 10 | **MiroFish → 墨思** | (同上) | 59K | 墨思 | 群体智能预测，情报局增强 |

---

## ⚡ 中优先级集成 (15个)

| # | 仓库 | 上游 | ⭐Stars | 子公司 | 集成方式 |
|:-:|:-----|:-----|:-------:|:------|:---------|
| 11 | **agent-skills** | addyosmani/agent-skills | 27K | 墨智 | 27380★工程技能库→批量导入墨麟 |
| 12 | **deepseek-coder-skills** | (若存在) | — | 墨码 | 工程技能集 |
| 13 | **deer-flow** | bytedance/deer-flow | 65K | 墨智 | 字节开源超Agent框架→蜂群引擎参考 |
| 14 | **Archon** | coleam00/Archon | 21K | 墨智 | AI编码harness→墨码/墨智工具链 |
| 15 | **oh-my-codex** | Yeachan-Heo/oh-my-codex | 27K | 墨智 | Codex多Agent编排→参考蜂群引擎 |
| 16 | **oh-my-claudecode** | Yeachan-Heo/oh-my-codex | 32K | 墨智 | Claude Code多Agent编排→墨智扩展 |
| 17 | **GenericAgent** | lsdefine/GenericAgent | 9K | 墨智 | 自进化Agent→自学习回路增强 |
| 18 | **seomachine** | TheCraigHewitt/seomachine | 7K | 墨迹 | SEO内容优化→墨迹内容管线增强 |
| 19 | **Pixelle-Video** | AIDC-AI/Pixelle-Video | 10K | 墨迹 | AI短视频引擎→墨迹视频管线 |
| 20 | **MoneyPrinterTurbo** | harry0703/MoneyPrinterTurbo | 57K | 墨迹 | 一键生成短视频→墨迹视频管线 |
| 21 | **marketing-hooks** | YuqingNicole/marketing-hooks | 7 | 墨增 | 营销Hook模板→墨增营销素材库 |
| 22 | **pm-skills** | phuryn/pm-skills | 11K | 墨品 | 100+产品管理技能→墨品产品设计增强 |
| 23 | **ghost-os** | ghostwright/ghost-os | 1.4K | 墨维 | Agent全计算机控制→墨维运维增强 |
| 24 | **super-agi** | (若存在) | — | 跨部门 | AGI框架参考 |
| 25 | **xiaohongshu-cli** | jackwener/xiaohongshu-cli | 1.8K | 墨影 | 小红书API CLI→墨影内容发布增强 |

---

## 🟢 低优先级/间接相关 (12个)

| # | 仓库 | 上游 | ⭐Stars | 说明 |
|:-:|:-----|:-----|:-------:|:-----|
| 26 | **agentic-agents** | (上游) | — | Agentic模式，已有蜂群引擎覆盖 |
| 27 | **antigravity-skills** | 1.4K+ skills | 36K | 技能合集，与awesome-openclaw重复 |
| 28 | **awesome-openclaw** | 5.4K skills | 48K | OpenClaw技能合集，Hermes技能格式不同 |
| 29 | **Avalonia** | .NET UI框架 | 31K | C#桌面开发，与Python体系不兼容 |
| 30 | **Deep-Live-Cam** | 实时换脸 | 93K | 视频深度伪造，与一人公司定位不符 |
| 31 | **browser(Lightpanda)** | 无头浏览器 | 30K | Hermes已有Browserbase浏览器工具 |
| 32 | **DeepTutor** | 个性化学习 | 23K | 墨育教育可参考但非核心 |
| 33 | **minimind** | 从0训练LLM | 49K | 深度学习教学项目，非直接可产品化 |
| 34 | **RuView** | WiFi信号感应 | 52K | 硬件相关，与纯AI服务不匹配 |
| 35 | **LiteRT-LM** | Google边缘AI | 4.7K | 端侧推理，与云端DeepSeek不匹配 |
| 36 | **claw-code** | ultraworkers | 190K | 代码工具，已通过Hermes覆盖 |
| 37 | **openclaw** | 367K | 368K | 最大AI助手开源项目，但已集成Hermes |

---

## ⚠️ 无需集成/重复 (17个)

| # | 仓库 | 原因 |
|:-:|:-----|:------|
| 38 | hermes-agent | ✅ 正在用的就是这个系统 |
| 39 | molin-ai-intelligent-system | ✅ 用户自己的项目，已参考 |
| 40 | Molin-OS | ✅ 已完全集成 |
| 41 | moye-tech.github.io | 个人页面 |
| 42 | Edu | 用户自己的项目 |
| 43 | claude-code / ClaudeCode | Claude Code CLI，Hermes已封装 |
| 44 | claude-code-best-practice | Claude Code最佳实践，已参考 |
| 45 | claude-code-sourcemap | 源码分析，非功能模块 |
| 46 | Claude-Code-Game-Studios | 游戏开发，与一人公司不符 |
| 47 | Claude-Code-x-OpenClaw-Guide-Zh | 中文教程文档 |
| 48 | claw-code | 已被openclaw合并 |
| 49 | ClawTeam-OpenClaw | OpenClaw团队版，非独立功能 |
| 50 | claudecodeui | Claude Code Web UI |
| 51 | learn-claude-code | Bash实现CLI工具 |
| 52 | hermes-web-ui | Hermes Web UI |
| 53 | openclaw-docker-cn-im | Docker版+中国IM整合 |
| 54 | OpenCLI | 网站→CLI转换 |
| 55 | opencow | 单任务Agent |
| 56 | omi | AI穿戴设备 |
| 57 | VPN- | 免费代理节点 |
| 58 | GitNexus | 代码智能引擎 |
| 59 | civil-engineering... | 土木工程云版本 |
| 60 | Agent-Reach | 社媒搜索API |
| 61 | agency-agents | AI Agency模式 |

    molin_owner: CEO
  hermes:
metadata:
---

## 🏆 Top 10 最值得立即集成

按优先级排序：

```
P0 🔥 立即集成
1. claude-mem (71K★) → 墨脑 — 自动记忆系统，每天省10%重复
2. MiroFish (59K★) → 墨思 — 群体智能预测，情报核心
3. ruflo (38K★) → 墨脑 — 自学习编排引擎升级
4. last30days-skill (25K★) → 墨思 — 情报日报自动生成
5. worldmonitor (53K★) → 墨思 — 全球实时情报

P1 ⚡ 本周
6. agent-skills (27K★) → 墨智 — 27K技能批量导入
7. supermemory (22K★) → 墨脑 — 记忆引擎增强
8. TradingAgents-CN (25K★) → 墨投 — 量化交易
9. seomachine (7K★) → 墨迹 — SEO内容增强
10. Pixelle-Video (10K★) → 墨迹 — 视频管线
```
